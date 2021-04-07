from datetime import date
import numpy as np
import networkx as nx
import pandas as pd
from abc import ABC, abstractmethod
from typing import NewType

from dfg_rating.model.betting.betting import BaseBetting
from dfg_rating.model.bookmaker.base_bookmaker import BaseBookmaker
from dfg_rating.utils.command_line import show_progress_bar
from dfg_rating.model.forecast.base_forecast import BaseForecast, SimpleForecast

TeamId = NewType('TeamId', int)


def weighted_winner(forecast: BaseForecast, match_data, home_team, away_team):
    f = abs(forecast.get_forecast(match_data, home_team, away_team))
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
        self.n_teams = self.params.get('teams', 0)
        self.n_rounds = self.params.get('rounds', self.n_teams - 1 + self.n_teams % 2)
        self.seasons = kwargs.get('seasons', 1)
        self.days_between_rounds = self.params.get('days_between_rounds', 1)

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
            for away_team, home_team, edge_attributes in sorted(filter(edge_filter, self.data.edges.data()),
                                                                key=lambda t: (t[2].get('season', 0), t[2]['round'], t[2]['day'])):
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
            if (print_kwargs.get('ratings', False)) & ('ratings' in self.data.nodes[np.random.choice(self.data.nodes())]):
                print("Teams ratings")
                for team in self.data.nodes:
                    print(f"Team {team} attributes:")
                    ratings_list = print_kwargs.get('ratings_list', [])
                    if len(ratings_list) == 0:
                        ratings_list = list(self.data.nodes[team]['ratings'].keys())
                    for rating in ratings_list:
                        print(f"Rating <{rating}> for team {team}: > {self.data.nodes[team].get('ratings', {}).get(rating, {})}")

    def iterate_over_games(self):
        return sorted(self.data.edges(keys=True, data=True), key=lambda t: (t[3].get('season', 0), t[3]['round']))

    def play_sub_network(self, games):
        for away_team, home_team, edge_key, edge_attributes in games:
            # Random winner with weighted choices
            if 'true_rating' not in self.data.nodes[away_team].get('ratings', {}):
                print('Error: Network needs true rating')
                pass
            if 'true_forecast' not in edge_attributes.get('forecasts', {}):
                print('Error: Network needs true forecast')
                pass
            winner = weighted_winner(edge_attributes['forecasts']['true_forecast'], edge_attributes, self.data.nodes[home_team], self.data.nodes[away_team])
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
        forecast.get_forecast(match_data, self.data.nodes[match[1]], self.data.nodes[match[0]], base_ranking)
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
        matches, forecasts = self._serialize_matches(network_name)
        serialized_network['networks'] = [{"network_name": network_name, "network_type": self.type}]
        serialized_network['matches'] = matches
        serialized_network['forecasts'] = forecasts
        serialized_network['ratings'] = self._serialize_ratings(network_name)
        return serialized_network

    def _serialize_matches(self, network_name):
        matches = []
        forecasts = []
        for away_team, home_team, edge_key, edge_attributes in self.iterate_over_games():
            new_match = {
                "network_name": network_name,
                "home_team": home_team,
                "away_team": away_team,
                "season": edge_attributes.get('season', 0),
                "round": edge_attributes.get('round', -1),
                "day": edge_attributes.get('day', -1),
                "winner": edge_attributes.get('winner', 'none'),
            }
            new_match["match_id"] = f"" \
                                   f"{new_match['home_team']}_vs_" \
                                   f"{new_match['away_team']}_" \
                                   f"{new_match['season']}_" \
                                   f"{new_match['day']}" \
                                   f""
            for f_name, f in edge_attributes.get('forecasts', {}).items():
                new_forecast = {
                    "forecast_name": f_name,
                    "network_name": network_name,
                    "match_id": new_match['match_id']
                }
                for i in range(len(f.outcomes)):
                    new_forecast[f"probability_{f.outcomes[i]}"] = f.probabilities[i]
                forecasts.append(new_forecast)
            matches.append(new_match)

        return matches, forecasts

    def _serialize_ratings(self, network_name):
        all_ratings = []
        for team in range(self.n_teams):
            team_dict = None
            try:
                team_dict = self.data.nodes[team]
            except Exception as e:
                print(f"Team {team} not in nodes")

            team_dict = team_dict or {}
            for rating_name, r in team_dict.get('ratings', {}).items():
                if rating_name != "hyper_parameters":
                    for season, ratings in r.items():
                        hyper_dict = team_dict.get('ratings', {}).get(
                            'hyper_parameters', {}
                        ).get(
                            rating_name, {}
                        ).get(
                            season, {}
                        )
                        for i, r in enumerate(ratings):
                            new_rating = {
                                "rating_name": rating_name,
                                "team_id": team,
                                "team_name": team_dict.get('name', team),
                                "network_name": network_name,
                                "season": season,
                                "rating_number": i,
                                "value": r,
                                "trend": hyper_dict.get('trends', [-1])[0],
                                "starting_point": hyper_dict.get('starting_points', [-1])[0]
                            }
                            all_ratings.append(new_rating)
        return all_ratings

    def deserialize_network(self, matches, forecasts, ratings):
        graph = nx.MultiDiGraph()
        max_season = 0
        max_round = 0
        max_day = 1
        for m in matches:
            edge_dict = {key: value for key, value in m.items()}
            max_day = edge_dict['day'] if edge_dict['round'] > max_round else max_day
            max_round = edge_dict['round'] if edge_dict['round'] > max_round else max_round
            max_season = edge_dict['season'] if edge_dict['season'] > max_round else max_round
            match_forecasts = [f for f in forecasts if f['match_id'] == m['match_id']]
            for f in match_forecasts:
                edge_dict.setdefault('forecasts', {})[f['forecast_name']] = SimpleForecast(
                        outcomes=['home', 'draw', 'away'],
                        probs=[f['probability_home'], f['probability_draw'], f['probability_away']]
                )
            graph.add_edge(m['away_team'], m['home_team'], **edge_dict)
        for r in ratings:
            graph.nodes[int(r['team_id'])]['name'] = r['team_name']
            ratings_object = graph.nodes[int(r['team_id'])].setdefault(
                'ratings', {}
            ).setdefault(r['rating_name'], {})
            ratings_object.setdefault(
                int(r['season']), []
            ).append(r['value'])

            graph.nodes[int(r['team_id'])].setdefault(
                'ratings', {}
            ).setdefault(
                'hyper_parameters', {}
            ).setdefault(
                r['rating_name'], {}
            ).setdefault(
                int(r['season']), {"trends": [r['trend']], "starting_points": [r['starting_point']]}
            )
        self.data = graph
        self.n_rounds = max_round + 1
        self.seasons = max_season + 1
        self.days_between_rounds = max_day / self.n_rounds

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

    def export(self, **kwargs):
        print("Export network")
        network_flat = []
        printing_forecasts = kwargs.get("forecasts", ['true_forecast'])
        printing_ratings = kwargs.get("ratings", ['true_rating'])
        for away_team, home_team, edge_key, edge_attributes in self.iterate_over_games():
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
                    match_dict[f"{r}#{name}"] = rating_dict.get(edge_attributes.get('season', 0))[edge_attributes.get('round', 0)]
            network_flat.append(match_dict)
        file_name = kwargs.get('filename', 'network.csv')
        df = pd.DataFrame(network_flat)
        df.to_csv(file_name, index=False)


    @abstractmethod
    def add_rating(self, new_rating, rating_name):
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
                self.table_data[self.mapping['day']] = pd.to_datetime(self.table_data[self.mapping['day']])
                self.table_data['Year'] = pd.DatetimeIndex(self.table_data[self.mapping['day']]).year
                self.table_data.sort_values(by=self.mapping['day'], inplace=True)
            else:
                self.table_data.sort_values(by=self.mapping['day'], inplace=True)
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
        day = 0
        daily_rankings = {}
        for row_id, row in self.table_data.iterrows():
            if self.mapping['dayIsTimestamp']:
                if day == 0:
                    day = 1
                    first_date = row[self.mapping['day']]
                else:
                    delta = row[self.mapping['day']] - first_date
                    day = delta.days
            else:
                day = int(row[self.mapping['day']])
            # Add edge (create if needed the nodes and attributes)
            edge_dict = {key: value for key, value in row.items()}
            edge_dict['day'] = day
            edge_dict['round'] = edge_dict.get(self.mapping['round'], 0) if 'round' in self.mapping else 0
            edge_dict['season'] = edge_dict.get(self.mapping['season'], 0) if 'season' in self.mapping else 0
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
                    if node_property_key not in ['id', 'rankings']:
                        graph.nodes[row[self.mapping[n]['id']]][node_property_key] = row[row_column]
                    elif node_property_key == 'rankings':
                        for ranking_name, ranking_column in row_column.items():
                            daily_rankings.setdefault(
                                ranking_name, {}
                            ).setdefault(
                                edge_dict['season'], {}
                            ).setdefault(
                                day, {}
                            )[row[self.mapping[n]['id']]] = row[ranking_column]

        for ranking_name, ranking_info in daily_rankings.items():
            for season_id, season_info in ranking_info.items():
                for day_number, day_info in season_info.items():
                    for t in graph.nodes():
                        if t in day_info:
                            node_value = day_info[t]
                        else:
                            node_value = graph.nodes[t].get('ratings', {}).get(ranking_name, {}).get(season_id, [0])[-1]
                        graph.nodes[t].setdefault(
                            "ratings", {}
                        ).setdefault(
                            ranking_name, {}
                        ).setdefault(
                            season_id, []
                        ).append(node_value)
        self.data = graph
        return True

    def add_rating(self, new_rating, rating_name):
        pass

    def add_forecast(self, forecast: BaseForecast, forecast_name, base_ranking):
        pass

    def add_odds(self, bookmaker_name: str, bookmaker: BaseBookmaker):
        pass

    def add_bets(self, bettor_name: str, bookmaker: str, betting: BaseBetting, base_forecast: str):
        pass

