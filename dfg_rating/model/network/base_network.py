import numpy as np
from abc import ABC, abstractmethod
from typing import NewType

from dfg_rating.model.forecast.base_forecast import BaseForecast

TeamId = NewType('TeamId', int)

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

    def play_data(self, forecast: BaseForecast):
        for away_team, home_team, edge_attributes in self.iterate_over_games():
            # TODO construct an object Match
            match_forecast = forecast.get_forecast()
            # Now the winner is the option with higher forecast
            winner = np.argmax(match_forecast)
            if winner == 0:
                self.data.edges[away_team, home_team]['winner'] = home_team
            elif winner == 1:
                self.data.edges[away_team, home_team]['winner'] = away_team
            else:
                self.data.edges[away_team, home_team]['winner'] = -1

