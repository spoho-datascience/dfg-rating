from dfg_rating.model import factory
from dfg_rating.model.network.base_network import BaseNetwork

network: BaseNetwork = factory.new_network(
    'multiple-round-robin',
    teams=20,
    days_between_rounds=3,
    seasons=4,
    league_teams=20,
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
    filename='network_first.csv'
)
# 1. network.iterate_over_games() -> returns a list of tuples with the games info (away, home, id (to be ignored), round, edge_dict)
network_games = network.iterate_over_games()
for away_id, home_id, match_id, edge_dict in network_games:
    # The problem here is that for each team you don't have the rating at that round so you need to go and pick it up.
    round = edge_dict['round']
    season = edge_dict['season']
    home_true_rating = network.data.nodes[home_id]['ratings']['true_rating'][season][round]
    away_true_rating = network.data.nodes[away_id]['ratings']['true_rating'][season][round]
    # Same goes for the elo_ratings
    
    # At the end you can add this differences to the edge_info (but you have to interact directly with the network)
    network.data.edges[(away_id, home_id, match_id)].setdefault('metrics', {})['true_rating_diff'] = home_true_rating - away_true_rating

# By adding the differences as a metric in the edge you can export using the existing functions:
network.export(
    forecasts=['true_forecast'],
    ratings=['true_rating', 'elo_rating'],
    metrics=['true_rating_diff'],
    filename='network_with_diff.csv'
)

# WHAT WE TALKED TODAY:
# Little structure to iterate over the all nodes and combine their arrays
network_seasons = network.get_seasons()
# Here you can play with the end result
for n in network.data.nodes:
    for season in network_seasons:
        team_true_rating = network.nodes[n]['ratings']['true_rating'][season]
        team_elo_rating = network.nodes[n]['ratings']['elo_rating'][season]
        for internal_n in network.data.nodes:
            if internal_n != n:
                diff_true_rating = team_true_rating - network.data.nodes[internal_n]['ratings']['true_rating'][season]
                diff_elo_rating = team_elo_rating - network.data.nodes[internal_n]['ratings']['elo_rating'][season]
                # Here you have the true differences and the elo difference between team n and team internal_n, do as you wish






