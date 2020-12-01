from dfg_rating.model.forecast.base_forecast import SimpleForecast
from dfg_rating.model.forecast.true_forecast import LogFunctionForecast
from dfg_rating.model.network.simple_network import RoundRobinNetwork
from dfg_rating.model.rating.controlled_trend_rating import ControlledTrendRating, ControlledRandomFunction

f_log = LogFunctionForecast(outcomes=['home', 'draw', 'away'], coefficients=[-0.9, 0.3])
rr_network = s = RoundRobinNetwork(
    teams=6,
    days_between_rounds=3
)
rr_network.create_data()
tested_rating = ControlledTrendRating(
    starting_point=ControlledRandomFunction(distribution='normal', loc=1000, scale=200),
    delta=ControlledRandomFunction(distribution='normal', loc=0, scale=3),
    trend=ControlledRandomFunction(distribution='normal', loc=0, scale=75),
    season_delta=ControlledRandomFunction(distribution='normal', loc=0, scale=10)
)

rr_network.add_rating(tested_rating, 'true_rating')

for away_team, home_team, match_key, match_data in rr_network.iterate_over_games():
    f_log.get_forecast(match_data, rr_network.data.nodes[home_team], rr_network.data.nodes[away_team])
    print(f_log.print())