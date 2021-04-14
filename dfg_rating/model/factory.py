from dfg_rating.model.betting.betting import FixedBetting
from dfg_rating.model.bookmaker.base_bookmaker import BookmakerMargin, SimpleBookmaker
from dfg_rating.model.forecast.base_forecast import SimpleForecast, BaseForecast
from dfg_rating.model.forecast.forecast_error import ForecastFactorError, ForecastSimulatedError
from dfg_rating.model.forecast.true_forecast import LogFunctionForecast
from dfg_rating.model.network.base_network import BaseNetwork
from dfg_rating.model.network.multiple_network import LeagueNetwork
from dfg_rating.model.network.simple_network import RoundRobinNetwork
from dfg_rating.model.rating.base_rating import BaseRating
from dfg_rating.model.rating.controlled_trend_rating import ControlledTrendRating, ControlledRandomFunction
from dfg_rating.model.rating.elo_rating import ELORating
from dfg_rating.model.rating.function_rating import FunctionRating
from dfg_rating.model.rating.ranking_rating import LeagueRating
from dfg_rating.model.rating.winner_rating import WinnerRating

pre_mappings = {
    "atp": {
        "node1": {
            "id": "WinnerID",
            "name": "Winner",
            "ratings": {
                "rank": "WRank",
                "Pts": "WPts"
            }
        },
        "node2": {
            "id": "LoserID",
            "name": "Loser",
            "ratings": {
                "rank": "LRank",
                "Pts": "LPts"
            }
        },
        "day": "Date",
        "dayIsTimestamp": True,
        "round": "Round",
        "season": "Year",
        'winner': {
            "id": "WinnerID"
        },
        "forecasts": {},
        "odds": {
            "b365": {
                "node1": "B365W",
                "node2": "B365L"
            }
        },
        "bets": {}
    },
    "soccer": {
        "node1": {
            "id": "Team away",
            "name": "Team away"
        },
        "node2": {
            "id": "Team home",
            "name": "Team home"
        },
        "day": "Date",
        "dayIsTimestamp": True,
        "round": "Round",
        "season": "Season",
        "forecasts": {},
        "odds": {},
        "bets": {}
    }
}


def new_network(network_type: str, **kwargs) -> BaseNetwork:
    """Create a network function

    Options:
     - single-soccer-simple: RoundRobinNetwork
    """
    if network_type == 'round-robin':
        return RoundRobinNetwork(**kwargs)
    elif network_type == 'multiple-round-robin':
        return LeagueNetwork(**kwargs)
    else:
        raise ValueError


def new_rating(rating_type: str, **kwargs) -> BaseRating:
    """Create a rating function

    Options:
     - random-function: FunctionRating
     - basic-winner: WinnerRating
    """
    if rating_type == 'random-function':
        return FunctionRating(**kwargs)
    elif rating_type == 'league-rating':
        return LeagueRating(**kwargs)
    elif rating_type == 'controlled-random':
        return ControlledTrendRating(**kwargs)
    elif rating_type == 'elo-rating':
        return ELORating(**kwargs)
    else:
        raise ValueError


def new_forecast(forecast_type: str, **kwargs) -> BaseForecast:
    """Create a forecast function

    Options:
     - simple: SimpleForecast
    """
    if forecast_type == 'simple':
        return SimpleForecast(**kwargs)
    if forecast_type == 'logistic-function':
        return LogFunctionForecast(**kwargs)
    else:
        raise ValueError


def new_forecast_error(error_type: str, **kwargs):
    """Create a forecast function

        Options:
         - simple: SimpleForecast
        """
    if error_type == 'factor':
        return ForecastFactorError(**kwargs)
    elif error_type == 'simulated':
        return ForecastSimulatedError(**kwargs)
    else:
        raise ValueError


def new_bookmaker_margin(margin_type: str, **kwargs):
    """Create a forecast function

        Options:
         - simple: SimpleForecast
        """
    if margin_type == 'simple':
        return BookmakerMargin(**kwargs)
    else:
        raise ValueError


def new_bookmaker(bookmaker_type: str, **kwargs):
    """Create a forecast function

        Options:
         - simple: SimpleForecast
        """
    if bookmaker_type == 'simple':
        return SimpleBookmaker(**kwargs)
    else:
        raise ValueError


def new_betting_strategy(betting_type: str, **kwargs):
    """Create a forecast function

        Options:
         - simple: SimpleForecast
        """
    if betting_type == 'fixed':
        return FixedBetting(**kwargs)
    else:
        raise ValueError


def new_class(class_name: str, **kwargs):
    if class_name == "controlled-random-function":
        return ControlledRandomFunction(**kwargs)

