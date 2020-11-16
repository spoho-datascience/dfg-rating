from abc import ABC, abstractmethod
from typing import NewType

from dfg_rating.model.network.base_network import BaseNetwork, TeamId, base_edge_filter


def get_rounds(games):
    """Helper function to retrieve the rounds of a list of games
    """
    rounds = set([data['day'] for a, h, k, data in games])
    return rounds


class BaseRating(ABC):
    """Abstract class defining the interface of Rating object.

    Attributes:
        rating_type (str): Text descriptor of the network type.
        params (dict): Dictionary of key-value parameters for the network configuration
    """

    def __init__(self, rating_type, **kwargs):
        self.type = rating_type
        self.params = kwargs

    @abstractmethod
    def get_all_ratings(self, n: BaseNetwork, edge_filter=base_edge_filter):
        """Computes the temporal rating of each team in a given network

        Args:
            :param n:
            :param edge_filter:
        """
        pass

    @abstractmethod
    def get_ratings(self, n: BaseNetwork, t: [TeamId], edge_filter=base_edge_filter):
        """Computes the temporal rating of a given set of teams in a given network

        Args:
            :param edge_filter:
            :param t:
            :param n:
        """
        print("Method not implemented for this class")
        pass
