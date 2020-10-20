from abc import ABC, abstractmethod


class BaseNetwork(ABC):
    """Abstract class defining the interface of Network object.
    A network is a set of nodes and edges defining the relationship between teams in a tournament.
    Teams can be modelled as individuals (Tennis) or collective teams (soccer).
    An edge between two teams identifies a competition between them

    Attributes:
        type (str): Text descriptor of the network type.
        params (dict): Dictionary of key-value parameters for the network configuration

    """

    def __init__(self, type, params):
        self.data = None
        self.type = type
        self.params = params

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
