from dfg_rating.model.network.simple_network import RoundRobinNetwork
from dfg_rating.model.rating.function_rating import FunctionRating


class Controller:
    """Execution controller for the simulator
    It manages all the commands sent to the model and stores all the staging entities.

    Attributes:
        inputs (Dict): Gathers each entity input parameters
    """
    inputs = {
        "network": {
            "simple": {
                "number_of_teams": {
                    "label": "Number of teams",
                    "type": int
                },
                "days_between_rounds": {
                    "label": "Days between rounds",
                    "type": int
                }
            }
        }
    }

    def __init__(self):
        self.networks = {}

    def print_network(self, name):
        if name in self.networks:
            n = self.networks[name]
            n.print_data()
            return True, ""
        else:
            return False, "Network not found"

    def new_network(self, name, n_type, params):
        n = RoundRobinNetwork(n_type, params)
        n.create_data()
        self.networks[name] = n
        return 1

    def add_new_rating(self, network_name: str, team_id: int, rating_type: str, rating_name, *rating_params):
        n = self.networks[network_name]
        print(rating_params[0])
        n.add_rating(FunctionRating(rating_params[0], rating_params[1:]), team_id, rating_name)

    def list(self, attribute):
        return [
            (element, self.__getattribute__(attribute)[element].type) for element in
            self.__getattribute__(attribute).keys()
        ]
