import numpy as np
from abc import ABC, abstractmethod
from typing import NewType

from dfg_rating.model.bookmaker.base_bookmaker import BaseBookmaker
from dfg_rating.model.forecast.base_forecast import BaseForecast

TeamId = NewType('TeamId', int)


def weighted_winner(forecast: BaseForecast):
    weights = forecast.get_forecast().cumsum()
    x = np.random.default_rng().uniform(0, 1)
    for i in range(len(weights)):
        if x < weights[i]:
            return forecast.outcomes[i]


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
                                                                key=lambda t: (t[2].get('season', 1), t[2]['round'])):
                if 'season' in edge_attributes:
                    if season_counter != edge_attributes['season']:
                        print(f"Season {edge_attributes['season']}")
                        season_counter = edge_attributes["season"]
                print(
                    f"({home_team} vs. {away_team} at round {edge_attributes['round']}, day {edge_attributes['day']})")
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
                    print(f"Team {team}:")
                    ratings_list = print_kwargs.get('ratings_list', [])
                    if len(ratings_list) == 0:
                        ratings_list = list(self.data.nodes[team]['ratings'].keys())
                    for rating in ratings_list:
                        print(f"Rating {rating} for team {team}: > {self.data.nodes[team]['ratings'][rating]}")

    def iterate_over_games(self):
        return sorted(self.data.edges.data(), key=lambda t: (t[2].get('season', 1), t[2]['round']))

    def play(self):
        for away_team, home_team, edge_attributes in self.iterate_over_games():
            # TODO construct an object Match
            # Random winner with weighted choices
            if 'true_forecast' not in edge_attributes['forecasts']:
                print("Playing season: Missing True forecast")
            winner = weighted_winner(edge_attributes['forecasts']['true_forecast'])
            self.data.edges[away_team, home_team]['winner'] = winner

    def _add_rating_to_team(self, team_id, rating_values, rating_name):
        self.data.nodes[team_id].setdefault('ratings', {})[rating_name] = rating_values

    def _add_forecast_to_team(self, match, forecast: BaseForecast, forecast_name):
        self.data.edges[match].setdefault('forecasts', {})[forecast_name] = forecast

    @abstractmethod
    def add_rating(self, new_rating, rating_name):
        pass

    @abstractmethod
    def add_forecast(self, forecast: BaseForecast, forecast_name):
        pass

    @abstractmethod
    def add_odds(self, bookmaker_name: str, bookmaker: BaseBookmaker):
        pass
