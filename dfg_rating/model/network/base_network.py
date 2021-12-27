import json
from copy import deepcopy
from datetime import date
import numpy as np
import networkx as nx
import pandas as pd
from abc import ABC, abstractmethod
from typing import NewType, Tuple, List

from numpy import int64

from dfg_rating.model.betting.betting import BaseBetting
from dfg_rating.model.bookmaker.base_bookmaker import BaseBookmaker
from dfg_rating.model.evaluators.base_evaluators import Evaluator
from dfg_rating.model.forecast.base_forecast import BaseForecast, SimpleForecast

from tqdm import tqdm

TeamId = NewType('TeamId', int)


def get_seasons(games):
    seasons = set([data['season'] for a, h, k, data in games])
    return seasons


def weighted_winner(forecast: BaseForecast, match_data, home_team, away_team, round_values):
    f = abs(forecast.get_forecast(match_data, home_team, away_team, round_values=round_values))
    weights = f.cumsum()
    x = np.random.default_rng().uniform(0, 1)
    for i in range(len(weights)):
        if x < weights[i]:
            return forecast.outcomes[i]


def base_edge_filter(edge):
    return True


class BaseNetwork(ABC):
    """Abstract class defining the interface of Network object.
    A network is a set of nodes and edges defining the relationship between teams in a tournament.
    Teams can be modelled as individuals (Tennis) or collective teams (soccer).
    An edge between two teams identifies a competition between them

    Attributes:
        network_type (str): Text descriptor of the network type.
        kwargs (dict): Dictionary of key-value parameters for the network configuration

    """

    def __init__(self, network_type: str, **kwargs):
        self.data = None
        self.type = network_type
        self.params = kwargs
        self.number_of_clusters = kwargs.get('clusters', 1)
        self.n_teams = self.params.get('teams', 0)
        self.n_rounds = self.params.get('rounds', self.n_teams - 1 + self.n_teams % 2)
        self.seasons = kwargs.get('seasons', 1)
        self.days_between_rounds = self.params.get('days_between_rounds', 1)

        from dfg_rating.model.rating.controlled_trend_rating import ControlledTrendRating, ControlledRandomFunction
        from dfg_rating.model.forecast.true_forecast import LogFunctionForecast

        self.true_rating = kwargs.get(
            'true_rating',
            ControlledTrendRating(
                starting_point=ControlledRandomFunction(distribution='normal', loc=1000, scale=150),
                delta=ControlledRandomFunction(distribution='normal', loc=0, scale=.5),
                trend=ControlledRandomFunction(distribution='normal', loc=0, scale=.2),
                season_delta=ControlledRandomFunction(distribution='normal', loc=0, scale=30)
            )
        )
        self.true_forecast = kwargs.get(
            'true_forecast',
            LogFunctionForecast(outcomes=['home', 'draw', 'away'], coefficients=[-0.9, 0.3], beta_parameter=0.006)
        )

    @abstractmethod
    def create_data(self):
        """Creates network data including teams and matches
        """
        pass

    def print_data(self, **print_kwargs):
        edge_filter = print_kwargs.get('edge_filter', base_edge_filter)
        if print_kwargs.get('schedule', False):
            print("Network schedule")
            season_counter = 0
            for away_team, home_team, edge_attributes in sorted(
                    filter(edge_filter, self.data.edges.data()),
                    key=lambda t: (t[2].get('season', 0), t[2]['round'], t[2]['day'])
            ):
                print(
                    f"({home_team} vs. {away_team} at season {edge_attributes['season']} round {edge_attributes['round']}, day {edge_attributes['day']})")
                if (print_kwargs.get('winner', False)) & ('winner' in edge_attributes):
                    print(f"Result: {edge_attributes['winner']}")
                if (print_kwargs.get('forecasts', False)) & ('forecasts' in edge_attributes):
                    forecasts_list = print_kwargs.get('forecasts_list', [])
                    if len(forecasts_list) == 0:
                        forecasts_list = list(edge_attributes['forecasts'].keys())
                    for forecast in forecasts_list:
                        print(f"Forecast {forecast}: {edge_attributes['forecasts'][forecast].print()}")
                if (print_kwargs.get('odds', False)) & ('odds' in edge_attributes):
                    bookmakers_list = print_kwargs.get('bookmakers_list', [])
                    if len(bookmakers_list) == 0:
                        bookmakers_list = list(edge_attributes['odds'].keys())
                    for bm in bookmakers_list:
                        print(f"Bookmaker {bm} odds: {edge_attributes['odds'][bm]}")
            print("---------------")
        if print_kwargs.get('attributes', False):
            if (print_kwargs.get('ratings', False)) & (
                    'ratings' in self.data.nodes[np.random.choice(self.data.nodes())]):
                print("Teams ratings")
                for team in self.data.nodes:
                    print(f"Team {team} attributes:")
                    ratings_list = print_kwargs.get('ratings_list', [])
                    if len(ratings_list) == 0:
                        ratings_list = list(self.data.nodes[team]['ratings'].keys())
                    for rating in ratings_list:
                        print(
                            f"Rating <{rating}> for team {team}: > {self.data.nodes[team].get('ratings', {}).get(rating, {})}")

    def get_seasons(self):
        return [s for s in range(self.seasons)]

    def get_rounds(self):
        return self.n_rounds * 2, [r for r in range(self.n_rounds * 2)]

    def iterate_over_games(self):
        return sorted(self.data.edges(keys=True, data=True), key=lambda t: (int(t[3].get('day', 0))))

    def play_sub_network(self, games):
        r, rv = self.get_rounds()
        for away_team, home_team, edge_key, edge_attributes in games:
            # Random winner with weighted choices
            if 'true_rating' not in self.data.nodes[away_team].get('ratings', {}):
                print('Error: Network needs true rating')
                pass
            if 'true_forecast' not in edge_attributes.get('forecasts', {}):
                print('Error: Network needs true forecast')
                pass
            winner = weighted_winner(
                edge_attributes['forecasts']['true_forecast'],
                edge_attributes,
                self.data.nodes[home_team],
                self.data.nodes[away_team],
                rv
            )
            self.data.edges[away_team, home_team, edge_key]['winner'] = winner

    def play(self):
        self.play_sub_network(self.iterate_over_games())

    def _add_rating_to_team(self, team_id, rating_values, rating_hyperparameters, rating_name, season=-1):
        if season is None:
            season = 0
        self.data.nodes[team_id].setdefault('ratings', {}).setdefault(rating_name, {})[season] = rating_values

        self.data.nodes[team_id].setdefault(
            'ratings', {}
        ).setdefault(
            'hyper_parameters', {}
        ).setdefault(
            rating_name, {}
        )[season] = rating_hyperparameters[team_id] if team_id in rating_hyperparameters else rating_hyperparameters

    def _add_forecast_to_team(self, match, forecast: BaseForecast, forecast_name, base_ranking):
        match_data = self.data.edges[match]
        n_rounds, round_values = self.get_rounds()
        forecast.get_forecast(
            match_data=match_data,
            home_team=self.data.nodes[match[1]],
            away_team=self.data.nodes[match[0]],
            base_ranking=base_ranking,
            round_values=round_values
        )
        self.data.edges[match].setdefault('forecasts', {})[forecast_name] = forecast

    def get_teams(
            self,
            ascending: bool = False,
            maximum_number_of_teams: int = None,
            in_league=True,
            ratings=None,
            season=None,
            round=None):
        if ratings is None:
            ratings = ['ranking']
            team_nodes = self.data.nodes
        maximum_number_of_teams = maximum_number_of_teams or self.n_teams
        if season is None:
            season = -1
        season_round = round if round is not None else self.n_rounds
        teams = {}
        set_of_nodes = [node for node in self.data.nodes if node in list(self.league_teams_labels.values())] \
            if in_league else [node for node in self.data.nodes]
        for node in set_of_nodes:
            for rating in ratings:
                try:
                    teams.setdefault(rating, []).append(
                        self.data.nodes[node].get('ratings', {}).get(rating, {}).get(season, {})[season_round - 1]
                    )
                    teams.setdefault('labels', []).append(node)
                except KeyError as K:
                    # log error
                    pass

        df = pd.DataFrame(teams).sort_values(by='ranking', ascending=ascending)
        df.set_index('labels', inplace=True)
        return df.head(maximum_number_of_teams).to_dict()['ranking']

    def serialize_network(self, network_name):
        serialized_network = {}
        matches, forecasts, odds, bets, metrics = self._serialize_matches(network_name)
        serialized_network['networks'] = [
            {
                "network_name": network_name,
                "network_type": self.type,
                "seasons": self.seasons,
                "days_between_rounds": self.days_between_rounds,
                "rounds": self.n_rounds
            },
        ]
        serialized_network['matches'] = matches
        serialized_network['forecasts'] = forecasts
        serialized_network['odds'] = odds
        serialized_network['bets'] = bets
        serialized_network['metrics'] = metrics
        serialized_network['ratings'] = self._serialize_ratings(network_name)
        return serialized_network

    def _serialize_matches(self, network_name):
        matches = []
        forecasts = []
        odds = []
        bets = []
        metrics = []
        for node1, node2, edge_key, edge_attributes in self.data.edges(keys=True, data=True):
            new_match = {
                "network_name": network_name,
                "node1": node1,
                "node2": node2,
                "season": edge_attributes.get('season', 0),
                "round": edge_attributes.get('round', -1),
                "day": edge_attributes.get('day', -1),
                "winner": edge_attributes.get('winner', 'none'),
            }
            new_match["match_id"] = f"" \
                                    f"{new_match['node1']}_vs_" \
                                    f"{new_match['node2']}_" \
                                    f"{new_match['season']}_" \
                                    f"{new_match['day']}" \
                                    f""
            for f_name, f in edge_attributes.get('forecasts', {}).items():
                new_forecast = {
                    "forecast_name": f_name,
                    "network_name": network_name,
                    "match_id": new_match['match_id'],
                    "attributes": {}
                }
                for i in range(len(f.outcomes)):
                    new_forecast["attributes"][f"probability_{f.outcomes[i]}"] = f.probabilities[i]
                new_forecast["attributes"] = json.dumps(new_forecast["attributes"])
                forecasts.append(new_forecast)
            for odd, values in edge_attributes.get('odds', {}).items():
                new_odd = {
                    "network_name": network_name,
                    "bookmaker_name": odd,
                    "match_id": new_match['match_id'],
                    "attributes": {}
                }
                for i, value in enumerate(values):
                    new_odd["attributes"][f"value_{i}"] = value
                new_odd["attributes"] = json.dumps(new_odd["attributes"])
                odds.append(new_odd)
            for bet, values in edge_attributes.get('bets', {}).items():
                new_bet = {
                    "bettor_name": bet,
                    "network_name": network_name,
                    "match_id": new_match['match_id'],
                    "attributes": {}
                }
                for i, value in enumerate(values):
                    new_bet["attributes"][f"value_{i}"] = value
                new_bet["attributes"] = json.dumps(new_bet["attributes"])
                bets.append(new_bet)
            for metric, values in edge_attributes.get('metrics', {}).items():
                new_metric = {
                    "metric_name": metric,
                    "network_name": network_name,
                    "match_id": new_match['match_id'],
                    "attributes": json.dumps(values)
                }
                metrics.append(new_metric)
            matches.append(new_match)

        return matches, forecasts, odds, bets, metrics

    def _serialize_ratings(self, network_name):
        all_ratings = []
        for node_id, node_info in self.data.nodes().items():
            for rating_name, r in node_info.get('ratings', {}).items():
                if rating_name != "hyper_parameters":
                    for season, ratings in r.items():
                        hyper_dict = node_info.get('ratings', {}).get(
                            'hyper_parameters', {}
                        ).get(
                            rating_name, {}
                        ).get(
                            season, {}
                        )
                        for i, r in enumerate(ratings):
                            new_rating = {
                                "rating_name": rating_name,
                                "node_id": node_id,
                                "node_name": node_info.get('name', node_id),
                                "network_name": network_name,
                                "season": season,
                                "rating_number": i,
                                "value": r,
                                "trend": hyper_dict.get('trends', [-1])[0],
                                "starting_point": hyper_dict.get('starting_points', [-1])[0]
                            }
                            all_ratings.append(new_rating)
        return all_ratings

    def deserialize_network(self, rounds, seasons, days, matches, forecasts, ratings, odds, bets, metrics):
        graph = nx.MultiDiGraph()
        self.n_rounds = rounds
        self.seasons = seasons
        self.days_between_rounds = days
        for m in tqdm(matches, leave=False):
            edge_dict = {key: value for key, value in m.items()}
            match_forecasts = [f for f in forecasts if f['match_id'] == m['match_id']]
            for f in match_forecasts:
                f_attributes = f['attributes']
                edge_dict.setdefault('forecasts', {})[f['forecast_name']] = SimpleForecast(
                    outcomes=['home', 'draw', 'away'],
                    probs=[f_attributes['probability_home'], f_attributes['probability_draw'], f_attributes['probability_away']]
                )
            for o in [match_odds for match_odds in odds if match_odds['match_id'] == m['match_id']]:
                edge_dict.setdefault('odds', {})[o['bookmaker_name']] = [v for v in o['attributes'].values()]
            for b in [match_bets for match_bets in bets if match_bets['match_id'] == m['match_id']]:
                edge_dict.setdefault('bets', {})[b['bettor_name']] = [v for v in b['attributes'].values()]
            for metric in [match_metrics for match_metrics in metrics if match_metrics['match_id'] == m['match_id']]:
                edge_dict.setdefault('metrics', {})[metric['metric_name']] = [
                    v for v in metric['attributes'].values()
                ] if (type(metric["attributes"]) == dict) else metric["attributes"]
            graph.add_edge(m['node1'], m['node2'], **edge_dict)
        for r in ratings:
            graph.nodes[r['node_id']]['name'] = r['node_name']
            ratings_object = graph.nodes[r['node_id']].setdefault(
                'ratings', {}
            ).setdefault(r['rating_name'], {})
            ratings_object.setdefault(
                r['season'], []
            ).append(r['value'])

            graph.nodes[r['node_id']].setdefault(
                'ratings', {}
            ).setdefault(
                'hyper_parameters', {}
            ).setdefault(
                r['rating_name'], {}
            ).setdefault(
                r['season'], {"trends": [r['trend']], "starting_points": [r['starting_point']]}
            )
        self.data = graph

    def get_number_of_teams(self):
        return len(self.data.nodes)

    def get_rankings(self):
        rankings_list = []
        for node in self.data.nodes:
            for rating_id, rating_value in self.data.nodes[node]['ratings'].items():
                if rating_id not in ['hyper_parameters'] + rankings_list:
                    rankings_list.append(rating_id)
        return rankings_list

    def get_forecasts(self):
        forecasts_list = []
        for edge in self.data.edges:
            forecasts_list += [f for f in self.data.edges[edge].get('forecasts', {}).keys() if f not in forecasts_list]
        return forecasts_list

    def add_evaluation(self, evaluators_list: List[Tuple[Evaluator, str]]):
        for away_team, home_team, match_id, match_attributes in self.data.edges(keys=True, data=True):
            for evaluator, evaluator_name in evaluators_list:
                correct, metric_value = evaluator.eval(match_attributes)
                if correct:
                    self.data.edges[(away_team, home_team, match_id)].setdefault(
                        'metrics', {}
                    )[evaluator_name] = metric_value
                else:
                    print(f"Incorrect output for metric {evaluator_name}")

    def export_ratings(self):
        ratings_value_list = {
            node: self.data.nodes[node].get('ratings', {}) for node in self.data.nodes
        }
        return ratings_value_list

    def degree(self, filter_active=False):
        if filter_active:
            subgraph = nx.MultiDiGraph(
                ((source, target, key) for source, target, key, attr in self.data.edges(keys=True, data=True) if attr.get('state', 'active') == 'active')
            )
            return subgraph.degree()
        else:
            return self.data.degree()

    def density(self, filter_active=False):
        if filter_active:
            subgraph = nx.MultiDiGraph(
                ((source, target, key) for source, target, key, attr in self.data.edges(keys=True, data=True) if attr.get('state', 'active') == 'active')
            )
            return nx.density(subgraph)
        else:
            return nx.density(self.data)



    def export(self, **kwargs):
        print("Export network")
        network_flat = []
        printing_forecasts = kwargs.get("forecasts", ['true_forecast'])
        printing_ratings = kwargs.get("ratings", ['true_rating'])
        printing_odds = kwargs.get("odds", [])
        printing_bets = kwargs.get("bets", [])
        printing_metrics = kwargs.get("metrics", [])
        for away_team, home_team, edge_key, edge_attributes in self.data.edges(keys=True, data=True):
            match_dict = {
                "Home": home_team,
                "Away": away_team,
                "Season": edge_attributes.get('season', 0),
                "Round": edge_attributes.get('round', -1),
                "Day": edge_attributes.get('day', -1),
                "Result": edge_attributes.get('winner', 'none'),
            }
            for f in printing_forecasts:
                forecast_object: BaseForecast = edge_attributes.get('forecasts', {}).get(f, None)
                if forecast_object is not None:
                    for i, outcome in enumerate(forecast_object.outcomes):
                        match_dict[f"{f}#{outcome}"] = forecast_object.probabilities[i]
            for r in printing_ratings:
                for team, name in [(home_team, 'Home'), (away_team, 'Away')]:
                    rating_dict = self.data.nodes[team].get('ratings', {}).get(r)
                    match_dict[f"{r}#{name}"] = rating_dict.get(edge_attributes.get('season', 0))[
                        edge_attributes.get('round', 0)]
            for o in printing_odds:
                for i, value in enumerate(edge_attributes.get('odds', {}).get(o, [])):
                    match_dict[f"{o}#odds#{i}"] = value
            for b in printing_bets:
                for i, value in enumerate(edge_attributes.get('bets', {}).get(b, [])):
                    match_dict[f"{b}#bets#{i}"] = value
            for m in printing_metrics:
                match_dict[f"{m}#metric"] = edge_attributes.get('metrics', {}).get(m, -1)
            network_flat.append(match_dict)
        file_name = kwargs.get('filename', 'network.csv')
        df = pd.DataFrame(network_flat)
        df.to_csv(file_name, index=False)

    @abstractmethod
    def add_rating(self, rating, rating_name):
        pass

    @abstractmethod
    def add_forecast(self, forecast: BaseForecast, forecast_name, base_ranking):
        pass

    @abstractmethod
    def add_odds(self, bookmaker_name: str, bookmaker: BaseBookmaker, base_forecast: str):
        pass

    @abstractmethod
    def add_bets(self, bettor_name: str, bookmaker: str, betting: BaseBetting, base_forecast: str):
        pass


class WhiteNetwork(BaseNetwork):
    """Fully flexible network to be created out of a table structure"""
    DEFAULT_MAPPING = {
        "node1": dict,
        "node2": dict,
        "day": str,
        "dayIsTimestamp": bool,
        "round": str
    }

    DEFAULT_NODE = {
        "id": str,
    }

    def __init__(self, **kwargs):
        super().__init__("white", **kwargs)
        self.table_data: pd.DataFrame = kwargs['data']
        self.mapping = kwargs.get("mapping", self.DEFAULT_MAPPING)
        correct, report = self.validate()
        if correct:
            if self.mapping['dayIsTimestamp']:
                self.table_data[self.mapping['day']] = pd.to_datetime(
                    self.table_data[self.mapping['day']],
                    format=self.mapping['ts_format']
                )
                self.table_data['Year'] = pd.DatetimeIndex(self.table_data[self.mapping['day']]).year
                self.table_data.sort_values(by=self.mapping['day'], inplace=True)
            else:
                self.table_data.sort_values(by=self.mapping['day'], inplace=True)
            self.season_values = [s for s in self.table_data[self.mapping['season']].unique()]
            self.create_data()
            print("Network loaded correctly")
        else:
            print("Errors in mapping:")
            for r in report:
                print(r)

    def validate(self):
        correct = True
        messages = []
        for first_level_key, first_level_type in self.DEFAULT_MAPPING.items():
            if first_level_key not in self.mapping:
                correct = False
                messages.append(f"Attribute {first_level_key} not present in mapping")
            elif type(self.mapping[first_level_key]) != first_level_type:
                correct = False
                messages.append(f"Attribute {first_level_key} in mapping should specify a {first_level_type}")
        if correct:
            for node_key, node_type in self.DEFAULT_NODE.items():
                for n in ["node1", "node2"]:
                    if node_key not in self.mapping[n]:
                        correct = False
                        messages.append(f"Attribute {node_key} not present in node definition")
                    elif type(self.mapping[n][node_key]) != node_type:
                        correct = False
                        messages.append(f"Attribute {node_key} in mapping should specify a {node_type}")
        if correct:
            for entity in ["forecasts", "odds", "bets"]:
                if type(self.mapping.get(entity, {})) == dict:
                    for entity_key, entity_value in self.mapping.get(entity, {}).items():
                        if type(entity_value) != dict:
                            correct = False
                            messages.append(f"<{entity}> must be specified as a dictionary")
                        else:
                            values = list(entity_value.values())
                            if any(type(v) != str for v in values):
                                correct = False
                                messages.append(f"<{entity}>: keys are outcomes and values columns")
                else:
                    correct = False
                    messages.append(f"<{entity}> syntax error at mapping")
        return correct, messages

    def create_data(self):
        graph = nx.MultiDiGraph()
        day = -1
        daily_ratings = {}
        self.round_values = []
        current_season = -1
        for row_id, row in self.table_data.iterrows():
            row_season = row[self.mapping['season']]
            if current_season != row_season:
                current_season = row_season
                day = -1
            if self.mapping['dayIsTimestamp']:
                if day == -1:
                    first_date = row[self.mapping['day']]
                delta = row[self.mapping['day']] - first_date
                day = delta.days
            else:
                day = int(row[self.mapping['day']])
            # Add edge (create if needed the nodes and attributes)
            edge_dict = {key: value for key, value in row.items()}
            edge_dict['day'] = day
            edge_dict['round'] = edge_dict.get(self.mapping['round'], '0') if 'round' in self.mapping else '0'
            edge_dict['season'] = edge_dict.get(self.mapping['season'], '0') if 'season' in self.mapping else '0'
            if edge_dict['round'] not in self.round_values:
                self.round_values.append(edge_dict['round'])
            if 'winner' in self.mapping:
                winner_mapping = self.mapping.get('winner', {})
                if 'id' in winner_mapping:
                    winner_id = winner_mapping.get('id')
                    for n in ['node1', 'node2']:
                        node_id = self.mapping[n]['id']
                        if winner_id == node_id:
                            edge_dict['winner'] = n
                elif 'result' in winner_mapping:
                    pointer_result = winner_mapping.get('result')
                    result_translation = winner_mapping.get('translation', {})
                    edge_dict['winner'] = result_translation.get(edge_dict.get(pointer_result, 'ErrorReadingResult'))
            for entity in ['forecasts', 'bets', 'odds']:
                for entity_name, entity_options in self.mapping.get(entity, {}).items():
                    values = [row[v] for v in entity_options.values()]
                    if entity == 'forecasts':
                        outcomes = list(entity_options.keys())
                        edge_dict.setdefault(entity, {})[entity_name] = SimpleForecast(
                            outcomes=outcomes,
                            probs=values
                        )
                    else:
                        edge_dict.setdefault(entity, {})[entity_name] = values
            graph.add_edge(row[self.mapping['node1']['id']], row[self.mapping['node2']['id']], **edge_dict)
            for n in ['node1', 'node2']:
                for node_property_key, row_column in self.mapping[n].items():
                    if node_property_key not in ['id', 'ratings']:
                        graph.nodes[row[self.mapping[n]['id']]][node_property_key] = row[row_column]
                    elif node_property_key == 'ratings':
                        for rating_name, rating_column in row_column.items():
                            daily_ratings.setdefault(
                                rating_name, {}
                            ).setdefault(
                                edge_dict['season'], {}
                            ).setdefault(
                                day, {}
                            )[row[self.mapping[n]['id']]] = row[rating_column]

        for rating_name, rating_info in daily_ratings.items():
            for season_id, season_info in rating_info.items():
                for day_number, day_info in season_info.items():
                    for t in graph.nodes():
                        if t in day_info:
                            node_value = day_info[t]
                        else:
                            node_value = graph.nodes[t].get('ratings', {}).get(rating_name, {}).get(season_id, [0])[-1]
                        graph.nodes[t].setdefault(
                            "ratings", {}
                        ).setdefault(
                            rating_name, {}
                        ).setdefault(
                            season_id, []
                        ).append(node_value)
        self.n_teams = len(graph.nodes)
        self.round_values = sorted(self.round_values)
        self.n_rounds = len(self.round_values)
        self.data = graph
        return True

    def get_seasons(self):
        return self.season_values

    def get_rounds(self):
        return self.n_rounds, self.round_values

    def add_rating(self, rating, rating_name, team_id=None, season=None):
        if season is not None:
            self.add_season_rating(rating, rating_name, team_id, season)
        else:
            for s_i, s in enumerate(self.get_seasons()):
                if isinstance(s, (int, np.integer)):
                    self.add_season_rating(rating, rating_name, team_id, s)
                else:
                    self.add_season_rating(rating, rating_name, team_id, s_i)

    def add_season_rating(self, rating, rating_name, team_id, season):
        def edge_filter(e):
            new_filter = (
                (e[3]['season'] == season)
            )
            return new_filter

        if team_id:
            rating_values, rating_hp = rating.get_ratings(
                self, [team_id], edge_filter
            )
            self._add_rating_to_team(team_id, rating_values, rating_hp, rating_name, season=season)
        else:
            ratings, rating_hp = rating.get_all_ratings(self, edge_filter, season)
            for team_i, team in enumerate(self.data.nodes):
                self._add_rating_to_team(int(team), ratings[team_i], rating_hp, rating_name, season=season)

    def add_forecast(self, forecast: BaseForecast, forecast_name, base_ranking='true_rating', season=None):
        for match in self.data.edges(keys=True):
            if (season is None) or (self.data.edges[match].get('season', 0) == season):
                self._add_forecast_to_team(match, deepcopy(forecast), forecast_name, base_ranking)

    def add_odds(self, bookmaker_name: str, bookmaker: BaseBookmaker, base_forecast: str):
        for away_team, home_team, edge_key, edge_attributes in self.data.edges(keys=True, data=True):
            if base_forecast not in edge_attributes['forecasts']:
                print(f"Missing <{base_forecast}> forecast in network")
            match_base_forecast = edge_attributes['forecasts'][base_forecast]
            base_probabilities = match_base_forecast.get_forecast(
                match_data=edge_attributes,
                home_team=self.data.nodes[home_team],
                away_team=self.data.nodes[away_team],
                round_values=self.get_rounds()[1]
            )
            self.data.edges[
                away_team, home_team, edge_key
            ].setdefault(
                'odds', {}
            )[bookmaker_name] = bookmaker.get_odds(base_probabilities)

    def add_bets(self, bettor_name: str, bookmaker: str, betting: BaseBetting, base_forecast: str):
        for away_team, home_team, edge_key, edge_attributes in self.data.edges(keys=True, data=True):
            if base_forecast not in edge_attributes['forecasts']:
                print(f"Missing <{base_forecast}< forecast.")
            bettor_forecast = edge_attributes['forecasts'][base_forecast]
            match_odds = edge_attributes.get('odds', {})[bookmaker]
            self.data.edges[
                away_team, home_team, edge_key
            ].setdefault(
                'bets', {}
            )[bettor_name] = betting.bet(bettor_forecast.probabilities, match_odds)
