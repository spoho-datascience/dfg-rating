from operator import indexOf

import numpy as np
from abc import abstractmethod

from dfg_rating.model.network.base_network import BaseNetwork, TeamId, base_edge_filter
from dfg_rating.model.rating.base_rating import BaseRating, get_rounds


class BaseRankingRating(BaseRating):
    """ Base Raking Rating class"""

    @abstractmethod
    def get_all_ratings(self, n: BaseNetwork, edge_filter=base_edge_filter, season=0):
        pass

    @abstractmethod
    def get_ratings(self, n: BaseNetwork, t: [TeamId], edge_filter=base_edge_filter):
        pass


class LeagueRating(BaseRankingRating):
    """ This class tries to emulate a common sport league Rating where each team receives a reward in terms of points
    depending on the result of the match.

    Attributes:
        results (List[str]): Possible results.
        points (List[float]): Reward for each type of result.
    """

    def __init__(self, **kwargs):
        super().__init__('LeagueRating', **kwargs)
        self.points_system = {}
        results = kwargs.get('results', ['win', 'lose', 'draw'])
        points = kwargs.get('points', [3, 0, 1])
        for i in range(len(results)):
            self.points_system[results[i]] = points[i]

    def get_all_ratings(self, league_network: BaseNetwork, edge_filter=None, season=0):
        edge_filter = edge_filter or base_edge_filter
        n_teams = league_network.n_teams
        games = league_network.data.edges(keys=True, data=True)
        n_rounds = len(get_rounds(games))
        ratings = np.zeros([n_teams, n_rounds + 1])
        current_round = -1
        for away_team, home_team, match_key, data in sorted(filter(edge_filter, games), key=lambda edge: edge[3]['round']):
            # In the case that a team is not playing that round, we make sure it gets the same rating as before.
            if int(data['round']) != current_round:
                current_round = data['round']
                for t in range(n_teams):
                    ratings[t][current_round + 1] = ratings[t][current_round]

            ratings[away_team][data['round'] + 1] = ratings[away_team][data['round']] + (
                self.points_system['win'] if data['winner'] == 'away'
                else self.points_system['draw'] if data['winner'] == 'draw'
                else self.points_system['lose']
            )
            ratings[home_team][data['round'] + 1] = ratings[home_team][data['round']] + (
                self.points_system['win'] if data['winner'] == 'home'
                else self.points_system['draw'] if data['winner'] == 'draw'
                else self.points_system['lose']
            )

        return ratings, self.points_system

    def get_ratings(self, league_network: BaseNetwork, team: [TeamId], edge_filter=None):
        edge_filter = edge_filter or base_edge_filter
        home_games = list(league_network.data.in_edges(team, keys=True, data=True))
        away_games = list(league_network.data.out_edges(team, keys=True, data=True))
        n_rounds = len(get_rounds(home_games + away_games))
        ratings = np.zeros([len(team), n_rounds + 1])
        for away_team, home_team, data in sorted(filter(edge_filter, home_games + away_games), key=lambda x: x[2]['day']):
            if home_team in team:
                i_home_team = indexOf(team, home_team)
                ratings[i_home_team][data['round'] + 1] = ratings[i_home_team][data['round']] + (
                    self.points_system['win'] if data['winner'] == 'home'
                    else self.points_system['draw'] if data['winner'] == 'draw'
                    else self.points_system['lose']
                )
            if away_team in team:
                i_away_team = indexOf(team, away_team)
                ratings[i_away_team][data['round'] + 1] = ratings[i_away_team][data['round']] + (
                    self.points_system['win'] if data['winner'] == 'away'
                    else self.points_system['draw'] if data['winner'] == 'draw'
                    else self.points_system['lose']
                )
        return ratings, self.points_system
