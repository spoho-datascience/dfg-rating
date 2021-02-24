from datetime import date
import numpy as np
import networkx as nx
import pandas as pd
from abc import ABC, abstractmethod
from typing import NewType

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
        if print_kwargs.get('schedule', False):
            print("Network schedule")
            season_counter = 0
            for away_team, home_team, edge_attributes in sorted(self.data.edges.data(),
                                                                key=lambda t: (t[2].get('season', 0), t[2]['round'])):
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
            if (print_kwargs.get('ratings', False)) & ('ratings' in self.data.nodes[0]):
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
        forecast.get_forecast(match_data, self.data.nodes[match[0]], self.data.nodes[match[1]], base_ranking)
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
        print(self.days_between_rounds)

    def get_number_of_teams(self):
        return len(self.data.nodes)

    def get_rankings(self):
        rankings_list = []
        for node in self.data.nodes:
            for rating_id, rating_value in self.data.nodes[node]['ratings'].items():
                if rating_id not in ['hyper_parameters'] + rankings_list:
                    rankings_list.append(rating_id)
        return rankings_list


    @abstractmethod
    def add_rating(self, new_rating, rating_name):
        pass

    @abstractmethod
    def add_forecast(self, forecast: BaseForecast, forecast_name, base_ranking):
        pass

    @abstractmethod
    def add_odds(self, bookmaker_name: str, bookmaker: BaseBookmaker):
        pass



class WhiteNetwork(BaseNetwork):
    """Fully flexible network to be created out of a table structure"""

    def __init__(self, **kwargs):
        super().__init__("white", **kwargs)
        self.table_data: pd.DataFrame = kwargs['data']
        self.table_data['Date'] = pd.to_datetime(self.table_data.Date)
        self.table_data.sort_values(by="Date", inplace=True)

    def create_data(self):
        graph = nx.DiGraph()
        sp = show_progress_bar(text="Loading network", start=True)
        day = 0
        for row_id, row in self.table_data.iterrows():
            if day == 0:
                day = 1
                first_date = row['Date']
            delta = row['Date'] - first_date
            day += delta.days
            # Add edge (create if needed the nodes and attributes)
            edge_dict = {key: value for key, value in row.items() if key not in ['WinnerID', 'LoserID']}
            edge_dict['day'] = day
            graph.add_edge(row['WinnerID'], row['LoserID'], **edge_dict)
            graph.nodes[row['WinnerID']]['name'] = row['Winner']
            graph.nodes[row['LoserID']]['name'] = row['Loser']
        show_progress_bar("Network Loaded", False, sp)
        self.data = graph
        return True

    def print_data(self, **print_kwargs):
        if print_kwargs.get('schedule', False):
            print("Network schedule")
            for away_team, home_team, edge_attributes in sorted(self.data.edges.data(), key=lambda t: t[2]['day']):
                print(f"({home_team} vs. {away_team} at Date {edge_attributes['Date']}, day {edge_attributes['day']})")

            print("---------------")
        if print_kwargs.get('attributes', False):
            for node in self.data.nodes:
                print(f"Node id: {node}, Name: {self.data.nodes[node]['name']}")

    def iterate_over_games(self):
        pass

    def add_rating(self, new_rating, rating_name):
        pass

    def add_forecast(self, forecast: BaseForecast, forecast_name, base_ranking):
        pass

    def add_odds(self, bookmaker_name: str, bookmaker: BaseBookmaker):
        pass