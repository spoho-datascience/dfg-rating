from typing import Dict

from dfg_rating.model import factory
from dfg_rating.model.betting.betting import BaseBetting
from dfg_rating.model.bookmaker.base_bookmaker import BookmakerError, BookmakerMargin, BaseBookmaker
from dfg_rating.model.network.base_network import BaseNetwork
from dfg_rating.model.rating.controlled_trend_rating import ControlledRandomFunction
from dfg_rating.model.rating.function_rating import FunctionRating


class Controller:
    """Execution controller for the simulator
    It manages all the commands sent to the model and stores all the staging entities.

    Attributes:
        inputs (Dict): Gathers each entity input parameters
    """
    inputs = {
        "network": {
            "round-robin": {
                "teams": {
                    "label": "Number of teams",
                    "type": int
                },
                "days_between_rounds": {
                    "label": "Days between rounds",
                    "type": int
                }
            }
        },
        "rating": {
            "random-function": {
                "distribution": {
                    "label": "Distribution method",
                    "type": str
                },
                "dist_args": {
                    "label": "Distribution args (arg1_name=arg1_value, argN_name=argN_value)",
                    "type": "custom_key_value",
                    "cast": "float"
                }
            },
            "basic-winner": {},
        },
        "forecast": {
            "simple": {
                "outcomes": {
                    "label": "Outcomes list",
                    "type": "custom_args_list"
                },
                "probs": {
                    "label": "Predefined probabilities",
                    "type": "custom_args_list",
                    "cast": "float"
                }
            }
        },
        "bookmaker": {
            "simple": {}
        },
        "bookmaker_error": {
            "factor": {
                "error": {
                    "label": "Deviation error",
                    "type": float
                },
                "scope": {
                    "label": "Error scope (positive | negative | both)",
                    "type": str
                }
            },
            "simulated": {
                "error": {
                    "label": "Bookmaker error distribution",
                    "type": str,
                },
                "error_args": {
                    "label": "Distribution args (arg1_name=arg1_value, argN_name=argN_value)",
                    "type": "custom_key_value",
                    "cast": "float"
                }
            }
        },
        "bookmaker_margin": {
            "base": {
                "margin": {
                    "label": "Bookmaker margin",
                    "type": float
                }
            }
        },
        "betting": {
            "fixed": {
                "bank_role": {
                    "label": "Bank role",
                    "type": float
                }
            }
        }
    }

    def __init__(self):
        self.networks: Dict[str, BaseNetwork] = {}
        self.bookmakers: Dict[str, BaseBookmaker] = {}
        self.bettings: Dict[str, BaseBetting] = {}

    def print_network(self, name, **kwargs):
        if name in self.networks:
            n = self.networks[name]
            n.print_data(**kwargs)
            return True, ""
        else:
            return False, "Network not found"

    def new_network(self, network_name: str, network_type: str, **kwargs):
        n = factory.new_network(network_type, **kwargs)
        n.create_data()
        self.networks[network_name] = n
        return 1

    def play_network(self, network_name: str):
        n = self.networks[network_name]
        n.play()

    def add_new_rating(self, network_name: str, rating_type: str, rating_name, **rating_kwargs):
        n = self.networks[network_name]
        new_rating = factory.new_rating(rating_type, **rating_kwargs)
        n.add_rating(new_rating, rating_name)

    def add_new_forecast(self, network_name: str, forecast_type: str, forecast_name: str, **forecast_kwargs):
        n = self.networks[network_name]
        new_forecast = factory.new_forecast(forecast_type, **forecast_kwargs)
        n.add_forecast(new_forecast, forecast_name)

    def list(self, attribute):
        return [
            (element, self.__getattribute__(attribute)[element].type) for element in
            self.__getattribute__(attribute).keys()
        ]

    def new_bookmaker_error(self, error_type, **error_kwargs):
        return factory.new_bookmaker_error(error_type, **error_kwargs)

    def new_bookmaker_margin(self, margin_type, **error_kwargs):
        return factory.new_bookmaker_margin(margin_type, **error_kwargs)

    def create_bookmaker(self, bookmaker_name: str, bookmaker_type: str, **kwargs):
        bm = factory.new_bookmaker(bookmaker_type, **kwargs)
        self.bookmakers[bookmaker_name] = bm

    def add_odds(self, network_name: str, bookmaker_name: str):
        n = self.networks[network_name]
        bm = self.bookmakers[bookmaker_name]
        n.add_odds(bookmaker_name, bm)

    def create_betting_strategy(self, betting_name: str, betting_type: str, **kwargs):
        bs = factory.new_betting_strategy(betting_type, **kwargs)
        self.bettings[betting_name] = bs

    def run_demo(self):
        """
        self.new_network(
            "test_network", "multiple-round-robin",
            teams=26, seasons=3, league_teams=18, league_promotion=3, days_between_rounds=3,
        )
        """
        self.new_network(
            "test_network", "round-robin",
            teams=18, days_between_rounds=10,
        )
        # """
