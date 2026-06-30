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
from dfg_rating.model.rating.player_elo_rating import PlayerELORating
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
        "ts_format": "%m/%d/%Y",
        "round": "day",
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
            "id": "AwayID",
            "name": "AwayTeam",
        },
        "node2": {
            "id": "HomeID",
            "name": "HomeTeam",
        },
        "day": "Date",
        "dayIsTimestamp": True,
        "ts_format": "%d.%m.%Y",
        "season": "Season",
        "winner": {
            "result": "ResultFT",
            "translation": {
                "H": "home",
                "D": "draw",
                "A": "away"
            }
        },
        "round": "day",
        "odds": {
            "maximumodds": {
                "home": "OddsHomeMax",
                "draw": "OddsDrawMax",
                "away": "OddsAwayMax"
            },
            "averageodds": {
                "home": "OddsHomeAvg",
                "draw": "OddsDrawAvg",
                "away": "OddsAwayAvg"
            },
        },
        "bets": {}
    },
    "player-soccer": {
        "node1": {
            "id": "away_team",
            "name": "away_team",
        },
        "node2": {
            "id": "home_team",
            "name": "home_team",
        },
        "day": "round",
        "dayIsTimestamp": False,
        "season": "season",
        "round": "round",
        "winner": {
            "result": "result",
            "translation": {
                "Home": "home",
                "Draw": "draw",
                "Away": "away"
            }
        },
        "lineups": {
            "n_slots": 4,
            "sides": {"home": "home", "away": "away"},
            "columns": {
                "player_id": "Player{i}_{side}",
                "minutes": "Player{i}_{side}_minutes",
                "goal_diff": "Player{i}_{side}_score",
                "start": "Player{i}_{side}_start_score",
                "end": "Player{i}_{side}_end_score"
            }
        },
        "forecasts": {},
        "odds": {},
        "bets": {}
    },
    "player-soccer-lists": {
        # Lineups stored as per-side list columns (JSON / Python literal), one entry
        # per player: see ``WhiteNetwork._roster_from_lists``. Used for real data such
        # as ``data_test.xlsx``. Expects a derived integer ``round`` column (e.g. the
        # chronological match index within the season) since the source has no rounds.
        "node1": {
            "id": "away_team",
            "name": "away_team",
        },
        "node2": {
            "id": "home_team",
            "name": "home_team",
        },
        "day": "round",
        "dayIsTimestamp": False,
        "season": "season_id",
        "round": "round",
        "winner": {
            "result": "result",
            "translation": {
                "home": "home",
                "draw": "draw",
                "away": "away"
            }
        },
        "lineups": {
            "mode": "lists",
            "drop_noise": True,
            "sides": {"home": "home", "away": "away"},
            "columns": {
                "player_list": "{side}_player_list",
                "minutes_list": "{side}_minutes_list",
                "goal_diff_list": "{side}_goal_diff_list"
            }
        },
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
    elif rating_type == 'player-elo':
        return PlayerELORating(**kwargs)
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

