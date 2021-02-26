from dfg_rating.model import factory
from dfg_rating.model.network.base_network import BaseNetwork

network: BaseNetwork = factory.new_network(
    'multiple-round-robin',
    teams=6,
    days_between_rounds=3,
    seasons=4,
    league_teams=6,
    league_promotion=0,
    create=True
)
network.add_rating(
    factory.new_rating("elo-rating", trained=True),
    "elo_rating"
)
network.export(
    forecasts=['true_forecast'],
    ratings=['true_rating', 'elo_rating'],
    filename='network.csv'
)
