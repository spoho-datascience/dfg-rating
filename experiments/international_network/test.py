import numpy as np
from dfg_rating.model.network.simple_network import RoundRobinNetwork
from dfg_rating.model.rating.controlled_trend_rating import ControlledRandomFunction, ControlledTrendRating
# from dfg_rating.model.rating.multi_mode_rating import ControlledRandomFunction, ControlledTrendRating
from dfg_rating.model.forecast.true_forecast import LogFunctionForecast
from dfg_rating.model.rating.elo_rating import ELORating

forecast_log = LogFunctionForecast(
    outcomes=['home', 'draw', 'away'],
    coefficients=[-0.9, 0.3],
    beta_parameter=.006
)

true_rating = ControlledTrendRating(
    random_number_generator=np.random.default_rng,
    starting_point=ControlledRandomFunction(
        distribution='normal', loc=1000, scale=80),
    delta=ControlledRandomFunction(
        distribution='normal', loc=0, scale=.2),
    trend=ControlledRandomFunction(
        distribution='normal', loc=0, scale=.1),
    season_delta=ControlledRandomFunction(
        distribution='normal', loc=0, scale=0)
)

robin_network = RoundRobinNetwork(
    teams=6,
    true_rating=true_rating,
    true_forecast=forecast_log,
    seasons=2
)

elo_rating = ELORating(
    rating_name='elo_rating',
    trained=True,
    rating_mode='keep',
    rating_mean=1000
)

robin_network.add_rating(elo_rating, 'elo_rating')

robin_network.export(ratings=['true_rating', 'elo_rating'],
                     filename='RoundRobinNetwork.csv')