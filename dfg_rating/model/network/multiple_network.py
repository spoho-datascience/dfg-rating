import networkx as nx
import random
from dfg_rating.model.bookmaker.base_bookmaker import BaseBookmaker
from dfg_rating.model.forecast.base_forecast import BaseForecast
from dfg_rating.model.network.simple_network import RoundRobinNetwork
from dfg_rating.model.rating.base_rating import BaseRating
from dfg_rating.model.rating.ranking_rating import LeagueRating


class LeagueNetwork(RoundRobinNetwork):
    """Network involving teams leagues

    Attributes:
        seasons: int -> Number of seasons
        league_teams: int -> Subset of teams competing in the league amount the pool teams. Default number of teams
        of the network
        league_promotion: int -> Number of teams to select for promotion and delegating. Default 1
        ranking_rating: str -> Name of the rating to consider the ranking of teams. Default is LeagueRanking'
        create: bool -> Boolean indicating to create the initial network if True. Default = True.
    """

    def __init__(self, **kwargs):
        kwargs['extra_type'] = 'multiple'
        super().__init__(**kwargs)
        self.seasons = kwargs.get('seasons', 1)
        self.league_teams = kwargs.get('league_teams', self.n_teams)
        self.league_promotion = kwargs.get('league_promotion', 1)
        self.league_teams_labels = {i: i for i in range(self.league_teams)}
        self.ranking_rating: BaseRating = kwargs.get('ranking_rating', LeagueRating())
        self.out_teams = self.n_teams - self.league_teams
        self.out_teams_labels = [self.league_teams + i for i in range(self.out_teams)]
        print(self.league_teams_labels, self.out_teams_labels)
        if kwargs.get('create', False):
            self.create_data()

    def create_data(self):
        for season in range(self.seasons):
            print(f"Season {season}")
            # Create the new season matches
            self.fill_graph(self.league_teams_labels, season=season)
            season_games = list(filter(lambda match: match[3].get('season', -1) == season, self.iterate_over_games()))
            # Simulate the execution of those matches
            self.play_sub_network(season_games)
            # Add league ranking to the teams with this new season
            self.add_rating(self.ranking_rating, 'ranking', season=season)
            promoted_items = random.sample(range(self.out_teams), self.league_promotion)
            promoted_teams = [self.out_teams_labels[promoted_items[i]] for i in range(self.league_promotion)]
            print(f"Promoted teams: {promoted_teams}")
            relegation_candidates = self.get_teams(ascending=True, maximum_number_of_teams=6, season=season)
            print(f"Relegation candidates: {relegation_candidates}")
            relegation_teams = random.sample(list(relegation_candidates.keys()), self.league_promotion)
            print(f"Relegation teams: {relegation_teams}")
            for i in range(len(promoted_teams)):
                for k, v in self.league_teams_labels.items():
                    if v == relegation_teams[i]:
                        self.league_teams_labels[k] = promoted_teams[i]
                        self.out_teams_labels.remove(promoted_teams[i])
                        self.out_teams_labels.append(v)
            print(self.league_teams_labels, self.out_teams_labels)

    def all_teams_have_rating(self, rating_key):
        return all(rating_key in self.data.nodes[n].get('ratings', {}) for n in self.data.nodes)

    def play(self):
        print("Multiple seasons is played when creating data")
        pass
