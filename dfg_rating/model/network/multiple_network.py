"""Networks including more than one season
"""
from dfg_rating.model.bookmaker.base_bookmaker import BaseBookmaker
from dfg_rating.model.forecast.base_forecast import BaseForecast
from dfg_rating.model.network.simple_network import RoundRobinNetwork
from dfg_rating.model.rating.base_rating import BaseRating


class LeagueNetwork(RoundRobinNetwork):
    """Network involving teams leagues

    Attributes:
        seasons: int -> Number of seasons
        league_teams: int -> Subset of teams competing in the league amount the pool teams
    """

    def __init__(self, **kwargs):
        super().__init__('multiple-league', **kwargs)
        self.seasons = kwargs.get('season', 1)
        self.league_teams = kwargs.get('league_teams', self.n_teams)
        self.out_teams = self.n_teams - self.league_teams

    def create_data(self):
        pass

    def print_data(self, **print_kwargs):
        pass

    def iterate_over_games(self):
        pass

    def add_rating(self, rating: BaseRating, rating_name, team_id=None):
        pass

    def add_forecast(self, forecast: BaseForecast, forecast_name):
        pass

    def add_odds(self, bookmaker_name: str, bookmaker: BaseBookmaker):
        pass
