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
        self.n_teams = self.params.get('number_of_teams', 0)
        self.n_rounds = self.params.get('rounds', self.n_teams - 1 + self.n_teams % 2)
        self.days_between_rounds = self.params.get('days_between_rounds', 1)

    @abstractmethod
    def create_data(self):
        """Creates network data including teams and matches
        """
        pass

    @abstractmethod
    def print_data(self, **kwargs):
        """Serialize and print via terminal the network content.
        """
        pass

    @abstractmethod
    def iterate_over_games(self):
        pass

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
