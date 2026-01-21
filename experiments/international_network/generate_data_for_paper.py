import random
import numpy as np

# --- Monkey Patch before any random import ---
SEED = 42

# 1. fix Python random
random.seed(SEED)

# 2. fix Numpy random
np.random.seed(SEED)

# 3. fix the default_rng use
_shared_rng = np.random.default_rng(SEED)
_original_default_rng = np.random.default_rng

# define a patched version of default_rng
def _patched_default_rng(seed=None):
    if seed is None:
        return _shared_rng
    return _original_default_rng(seed)

# use patch
np.random.default_rng = _patched_default_rng
# --- Monkey patch End ---

from dfg_rating.model.network.simple_network import RoundRobinNetwork
from dfg_rating.model.rating.controlled_trend_rating import ControlledRandomFunction, ControlledTrendRating
from dfg_rating.model.forecast.true_forecast import LogFunctionForecast

number_of_nodes = 400
rr_network = RoundRobinNetwork(
    teams=number_of_nodes,
    days_between_rounds=1,
    true_forecast=LogFunctionForecast(
        outcomes=['home', 'draw', 'away'],
        coefficients=[-0.9, 0.3],
        beta_parameter=0.006
    ),
    true_rating=ControlledTrendRating(
        starting_point=ControlledRandomFunction(distribution='normal', loc=1000, scale=100),
        delta=ControlledRandomFunction(distribution='normal', loc=0, scale=5),
        trend=ControlledRandomFunction(distribution='normal', loc=0, scale=0),
        season_delta=ControlledRandomFunction(distribution='normal', loc=0, scale=0),
        rating_name='true_rating'
    ),
)
rr_network.export(printing_ratings=['true_rating'],filename='test_42seed_roundrobin_network3.csv')
