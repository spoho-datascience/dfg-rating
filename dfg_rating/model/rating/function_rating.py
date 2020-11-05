import numpy as np

from dfg_rating.model.network.base_network import BaseNetwork, TeamId
from dfg_rating.model.rating.base_rating import BaseRating, get_rounds


class FunctionRating(BaseRating):
    """Rating based on function generation
    Functions follow standard NumPy names and args
    https://numpy.org/doc/stable/reference/random/generator.html

    Attributes:
        distribution (str): Function name
    """

    def __init__(self, rating_type: str, **args):
        super().__init__(rating_type)
        try:
            self.distribution_method = getattr(np.random.default_rng(), args['distribution'])
            args.pop('distribution', None)
        except AttributeError as attr:
            self.distribution_method = None
        self.arguments = args

    def get_all_ratings(self, n: BaseNetwork):
        n_teams = len(n.data)
        games = n.data.edges(data=True)
        n_rounds = len(get_rounds(games))
        ratings = np.empty((n_teams, n_rounds + 1))
        for i in range(0, n_teams):
            ratings[i] = self._compute_array(array_length=n_rounds + 1)
        return ratings

    def get_ratings(self, n: BaseNetwork, t: TeamId):
        pass

    def _compute(self):
        """Compute single rating"""
        if self.distribution_method is not None:
            s = self.distribution_method(self.arguments)
            return s

    def _compute_array(self, array_length):
        """Compute array of ratings"""
        new_args = self.arguments
        new_args['size'] = array_length
        if self.distribution_method is not None:
            s = self.distribution_method(**new_args)
            return s
