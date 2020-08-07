import numpy as np
import networkx as nx

import json

from model.network.base_network import BaseNetwork
from model.rating.base_rating import BaseRating


class WinnerRating(BaseRating):

    """Winner dummy rating adding 1 to the winner team rating.
    """

    def get_all(self, network: BaseNetwork):
        n_teams = len(network.data)
        games = network.data.edges(data=True)
        n_rounds = len(self._get_rounds(games))
        ratings = np.zeros([n_teams, n_rounds + 1])
        for away_team, home_team, data in sorted(games, key=lambda edge: edge[2]['day']):
            ratings[away_team][data['day'] + 1] = ratings[away_team][data['day']]
            ratings[home_team][data['day'] + 1] = ratings[home_team][data['day']]
            ratings[data['winner']][data['day'] + 1] += 1

        return ratings

    def get(self, network: BaseNetwork, team_id: int):
        games = list(network.in_edges(team_id, data=True)) + list(network.out_edges(team_id, data=True))
        n_rounds = len(self._get_rounds(games))
        ratings = np.zeros([len(team_id), n_rounds + 1])

        for away_team, home_team, data in sorted(games, key=lambda x: x[2]['day']):
            if data['winner'] in team_id:
                ratings[data['winner']][data['day'] + 1] = ratings[data['winner']][data['day']] + 1

        return ratings

    def _get_rounds(self, games):
        """Helper function to retrieve the rounds of a list of games
        """
        rounds = set([data['day'] for a, h, data in games])
        return rounds




if __name__ == '__main__':
    G = nx.DiGraph()
    matches_list = [
        (0, 3, {"day": 0, "winner": 0}),
        (1, 2, {"day": 0, "winner": 2}),
        (0, 2, {"day": 1, "winner": 0}),
        (1, 3, {"day": 1, "winner": 3}),
        (3, 0, {"day": 2, "winner": 0}),
        (2, 1, {"day": 2, "winner": 2}),
        (2, 0, {"day": 3, "winner": 0}),
        (3, 1, {"day": 3, "winner": 3})
    ]
    print(f"Network: {matches_list}")
    G.add_edges_from(matches_list)
    wr = WinnerRating('type', {})
    print("All ratings:")
    print(wr.get_all(G))
    t = [0,1]
    print(f"Rating of teams {t}")
    print(wr.get(G, t))
