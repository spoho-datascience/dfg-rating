import numpy as np
from abc import ABC, abstractmethod
from typing import NewType

from dfg_rating.model.forecast.base_forecast import BaseForecast

TeamId = NewType('TeamId', int)


def weighted_winner(forecast):
    weights = forecast.get_forecast().cumsum()
    x = np.random.default_rng().uniform(0, 1)
    print(weights)
    print(x)
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
        params (dict): Dictionary of key-value parameters for the network configuration

    """

    def __init__(self, network_type, params):
        self.data = None
        self.type = network_type
        self.params = params
        self.n_teams = self.params.get('number_of_teams', 0)
        self.n_rounds = self.params.get('rounds', self.n_teams - 1 + self.n_teams % 2)
        self.days_between_rounds = self.params.get('days_between_rounds', 1)

    @abstractmethod
    def create_data(self):
        """Creates network data including teams and matches
        """
        pass

    @abstractmethod
    def print_data(self):
        """Serialize and print via terminal the network content.
        """
        pass

    @abstractmethod
    def iterate_over_games(self):
        pass

    def play(self, forecast: BaseForecast):
        for away_team, home_team, edge_attributes in self.iterate_over_games():
            # TODO construct an object Match
            # Random winner with weighted choices
            winner = weighted_winner(forecast)
            self.data.edges[away_team, home_team]['winner'] = winner

