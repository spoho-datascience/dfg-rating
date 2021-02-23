from dfg_rating.model.forecast.base_forecast import SimpleForecast
from dfg_rating.model.forecast.true_forecast import LogFunctionForecast
from dfg_rating.model.network.multiple_network import LeagueNetwork
from dfg_rating.model.network.simple_network import RoundRobinNetwork
from dfg_rating.model.rating.controlled_trend_rating import ControlledTrendRating, ControlledRandomFunction
from dfg_rating.model.rating.ranking_rating import LeagueRating

f_log = LogFunctionForecast(outcomes=['home', 'draw', 'away'], coefficients=[-0.302, 0.870])
rr_network = s = LeagueNetwork(
    teams=4,
    days_between_rounds=3,
    seasons=1,
    league_teams=4,
    league_promotion=0,
    create=True
)
tested_rating = ControlledTrendRating(
    starting_point=ControlledRandomFunction(distribution='normal', loc=1000, scale=200),
    delta=ControlledRandomFunction(distribution='normal', loc=0, scale=3),
    trend=ControlledRandomFunction(distribution='normal', loc=0, scale=75),
    season_delta=ControlledRandomFunction(distribution='normal', loc=0, scale=10)
)

rr_network.add_rating(tested_rating, 'example_rating')
rr_network.add_forecast(f_log, "test_f")
"""rr_network.add_rating(LeagueRating(), 'league')
rr_network.add_forecast(f_log, "league-based", base_ranking='league')
"""
"""for away_team, home_team, match_key, match_data in rr_network.iterate_over_games():
    f_log.get_forecast(match_data, rr_network.data.nodes[home_team], rr_network.data.nodes[away_team], base_ranking='league')
    print(f_log.print(), f"Sum: {sum(f_log.probabilities)}")"""