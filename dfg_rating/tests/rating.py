from dfg_rating.model.network.simple_network import RoundRobinNetwork
from dfg_rating.model.rating.function_rating import FunctionRating
from dfg_rating.model.rating.winner_rating import WinnerRating

rr_network = s = RoundRobinNetwork(
    "type",
    {
        "number_of_teams": 5,
        "days_between_rounds": 3
    }
)
rr_network.create_data()

normal_rating = FunctionRating('normal', 10, 1)
print(type(normal_rating.get_all_ratings(rr_network)))
print(normal_rating.get_aldl_ratings(rr_network))

winner_rating = WinnerRating('winner')
print(type(winner_rating.get_all_ratings(rr_network)))
print(winner_rating.get_all_ratings(rr_network))
