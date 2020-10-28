from abc import ABC, abstractmethod
from typing import NewType

from dfg_rating.model.network.base_network import BaseNetwork, TeamId


def get_rounds(games):
    """Helper function to retrieve the rounds of a list of games
    """
    rounds = set([data['day'] for a, h, data in games])
    return rounds


class BaseRating(ABC):
    """Abstract class defining the interface of Rating object.

    Attributes:
        rating_type (str): Text descriptor of the network type.
        params (dict): Dictionary of key-value parameters for the network configuration
    """

    def __init__(self, rating_type, params={}):
        self.type = rating_type
        self.params = params

    @abstractmethod
    def get_all_ratings(self, n: BaseNetwork):
        """Computes the temporal rating of each team in a given network

        Args:
            n (Network): 
        """
        pass

    @abstractmethod
    def get_ratings(self, n: BaseNetwork, t: TeamId):
        """Computes the temporal rating of a given set of teams in a given network

        Args:
            n (Network): 
            t (list(int)): Team identifiers list
        """
        pass
