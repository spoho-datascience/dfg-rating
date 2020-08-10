from abc import ABC, abstractmethod


class BaseRating(ABC):

    """Abstract class defining the interface of Rating object.

    Attributes:
        rating_type (str): Text descriptor of the network type.
        params (dict): Dictionary of key-value parameters for the network configuration
    """

    def __init__(self, rating_type, params):
        self.type = rating_type
        self.params = params

    @abstractmethod
    def get_all(self, n):
        """Computes the temporal rating of each team in a given network

        Args:
            n (Network): 
        """
        pass

    @abstractmethod
    def get(self, n, t):
        """Computes the temporal rating of a given set of teams in a given network

        Args:
            n (Network): 
            t (list(int)): Team identifiers list
        """
        pass
