"""Networks including more than one season
"""
import networkx as nx
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
        if self.data is None:
            season_args = self.params
            season_args['teams'] = self.league_teams
            print(season_args)
            season_network = RoundRobinNetwork('subtype', **season_args)
            season_network.create_data()
            self.data = season_network.data
            for away_team, home_team, edge in self.iterate_over_games():
                self.data.edges[away_team, home_team]['season'] = 1

        if self.all_teams_have_true_rating():
            pass
        else:
            print("Cannot create network data: Missing true ratings")

        pass

    def add_rating(self, rating: BaseRating, rating_name, team_id=None):
        pass

    def add_forecast(self, forecast: BaseForecast, forecast_name):
        pass

    def add_odds(self, bookmaker_name: str, bookmaker: BaseBookmaker):
        pass

    def all_teams_have_true_rating(self):
        return all('true_rating' in self.data.nodes[n] for n in self.data.nodes)
