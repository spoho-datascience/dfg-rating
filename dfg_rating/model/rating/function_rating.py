import numpy as np

from dfg_rating.model.network.base_network import BaseNetwork, TeamId, base_edge_filter
from dfg_rating.model.rating.base_rating import BaseRating, get_rounds


class FunctionRating(BaseRating):
    """Rating based on function generation
    Functions follow standard NumPy names and args
    https://numpy.org/doc/stable/reference/random/generator.html

    Attributes:
        distribution (str): Function name
    """

    def __init__(self, **args):
        super().__init__('random-function')
        try:
            self.distribution_method = getattr(np.random.default_rng(), args['distribution'])
            args.pop('distribution', None)
        except AttributeError as attr:
            self.distribution_method = None
        self.arguments = args

    def get_all_ratings(self, n: BaseNetwork, edge_filter=None):
        edge_filter = edge_filter or base_edge_filter
        n_teams = len(n.data)
        games = filter(edge_filter, n.data.edges(keys=True, data=True))
        n_rounds = len(get_rounds(games))
        ratings = np.empty((n_teams, n_rounds + 1))
        for i in range(0, n_teams):
            ratings[i] = self._compute_array(array_length=n_rounds + 1)
        return ratings, self.rating_properties()

    def get_ratings(self, n: BaseNetwork, t: TeamId, edge_filter=None):
        pass

    def _compute(self):
        """Compute single rating"""
        if self.distribution_method is not None:
            s = self.distribution_method(self.arguments)
            return s, self.rating_properties()

    def _compute_array(self, array_length):
        """Compute array of ratings"""
        new_args = self.arguments
        new_args['size'] = array_length
        if self.distribution_method is not None:
            s = self.distribution_method(**new_args)
            return s

    def rating_properties(self, array_length=1):
        props = {"distribution_method": self.distribution_method, "array_length": array_length}
        for arg, value in self.arguments.items():
            props[arg] = value
        return props
