from dfg_rating.model.forecast.base_forecast import SimpleForecast
from dfg_rating.model.network.simple_network import RoundRobinNetwork
from dfg_rating.model.rating.ranking_rating import LeagueRating

rr = RoundRobinNetwork(
    'simple',
    teams=4,
    days_between_rounds=3
)
rr.create_data()
rr.add_forecast(SimpleForecast('simple', outcomes=['home', 'draw', 'away']), 'true_forecast')
rr.play()
ranking_rating = LeagueRating('leagueRating')
rr.print_data(schedule=True, winner=True)
print(ranking_rating.get_all_ratings(rr))
print(ranking_rating.get_ratings(rr, [0]))
print(ranking_rating.get_ratings(rr, [3]))
