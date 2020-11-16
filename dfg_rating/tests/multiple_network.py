from dfg_rating.model.network.multiple_network import LeagueNetwork
from dfg_rating.model.rating.function_rating import FunctionRating

multiple_network = LeagueNetwork(
    teams=8,
    seasons=2,
    league_teams=4,
    league_promotion=2
)
# multiple_network.add_rating(rating=FunctionRating(distribution='normal', loc=5, scale=1), rating_name='true_rating')
multiple_network.create_data()
multiple_network.print_data(schedule=True, winner=True, attributes=True, ratings=True, ratings_list=['ranking'])
