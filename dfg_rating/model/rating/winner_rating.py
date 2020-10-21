import numpy as np
import networkx as nx

from dfg_rating.model.network.base_network import BaseNetwork, TeamId
from dfg_rating.model.rating.base_rating import BaseRating, get_rounds


class WinnerRating(BaseRating):

    """Winner dummy rating adding 1 to the winner team rating.
    """

    def get_all(self, network: BaseNetwork):
        n_teams = len(network.data)
        games = network.data.edges(data=True)
        n_rounds = len(get_rounds(games))
        ratings = np.zeros([n_teams, n_rounds + 1])
        for away_team, home_team, data in sorted(games, key=lambda edge: edge[2]['day']):
            ratings[away_team][data['day'] + 1] = ratings[away_team][data['day']]
            ratings[home_team][data['day'] + 1] = ratings[home_team][data['day']]
            ratings[data['winner']][data['day'] + 1] += 1
        return ratings

    def get(self, network: BaseNetwork, team_id: TeamId):
        games = list(network.data.in_edges(team_id, data=True)) + list(network.data.out_edges(team_id, data=True))
        n_rounds = len(get_rounds(games))
        ratings = np.zeros([len(team_id), n_rounds + 1])
        for away_team, home_team, data in sorted(games, key=lambda x: x[2]['day']):
            if data['winner'] in team_id:
                ratings[data['winner']][data['day'] + 1] = ratings[data['winner']][data['day']] + 1
        return ratings


if __name__ == '__main__':
    pass
