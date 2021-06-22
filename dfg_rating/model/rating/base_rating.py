import numpy as np
from abc import ABC, abstractmethod

from dfg_rating.model.network.base_network import BaseNetwork, TeamId


def get_rounds(games):
    """Helper function to retrieve the rounds of a list of games
    """
    rounds = set([data['round'] for a, h, k, data in games])
    return rounds



def get_rounds_per_season(games):
    away, home, key, data = [g for g in games][0]
    first_season = data.get('season', 0)

    def filter_games(g):
        filter = (
            (g[3]['season'] == first_season)
        )
        return filter

    single_season = filter(filter_games, games)
    rounds = set([data['round'] for a, h, k, data in single_season])
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
        self.rating_mean = kwargs.get('rating_mean', 1000)

    @abstractmethod
    def get_all_ratings(self, n: BaseNetwork, edge_filter=None):
        """Computes the temporal rating of each team in a given network. Return the rating values and the rating
        hyperparameters.

        Args:
            :param n:
            :param edge_filter:
        """
        pass

    @abstractmethod
    def get_ratings(self, n: BaseNetwork, t: [TeamId], edge_filter=None):
        """Computes the temporal rating of a given set of teams in a given network. Return the rating values and
        the rating hyperparameters.

        Args:
            :param edge_filter:
            :param t:
            :param n:
        """
        print("Method not implemented for this class")
        pass


class RatingError(ABC):

    @abstractmethod
    def apply(self, r: float) -> float:
        pass


class RatingNullError(RatingError):

    def apply(self, r: float) -> float:
        return r


class RatingFunctionError(RatingError):

    def __init__(self, error, **kwargs):
        try:
            self.error_method = getattr(np.random.default_rng(), error)
        except AttributeError:
            print("Error method not available")
            return
        self.error_arguments = kwargs

    def apply(self, r: float) -> float:
        return r + self.error_method(**self.error_arguments)

