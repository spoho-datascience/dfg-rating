from dfg_rating.model.betting.betting import FixedBetting
from dfg_rating.model.bookmaker.base_bookmaker import FactorBookmakerError, BookmakerMargin, SimpleBookmaker, \
    SimulatedBookmakerError
from dfg_rating.model.forecast.base_forecast import SimpleForecast, BaseForecast
from dfg_rating.model.network.base_network import BaseNetwork
from dfg_rating.model.network.simple_network import RoundRobinNetwork
from dfg_rating.model.rating.base_rating import BaseRating
from dfg_rating.model.rating.controlled_trend_rating import ControlledTrendRating
from dfg_rating.model.rating.function_rating import FunctionRating
from dfg_rating.model.rating.winner_rating import WinnerRating


def new_network(network_type: str, **kwargs) -> BaseNetwork:
    """Create a network function

    Options:
     - single-soccer-simple: RoundRobinNetwork
    """
    if network_type == 'round-robin':
        return RoundRobinNetwork(**kwargs)
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
    elif rating_type == 'basic-winner':
        return WinnerRating(**kwargs)
    elif rating_type == 'controlled-random':
        return ControlledTrendRating(**kwargs)
    else:
        raise ValueError


def new_forecast(forecast_type: str, **kwargs) -> BaseForecast:
    """Create a forecast function

    Options:
     - simple: SimpleForecast
    """
    if forecast_type == 'simple':
        return SimpleForecast(**kwargs)
    else:
        raise ValueError


def new_bookmaker_error(error_type: str, **kwargs):
    """Create a forecast function

        Options:
         - simple: SimpleForecast
        """
    if error_type == 'factor':
        return FactorBookmakerError(**kwargs)
    elif error_type == 'simulated':
        return SimulatedBookmakerError(**kwargs)
    else:
        raise ValueError


def new_bookmaker_margin(margin_type: str, **kwargs):
    """Create a forecast function

        Options:
         - simple: SimpleForecast
        """
    if margin_type == 'base':
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
