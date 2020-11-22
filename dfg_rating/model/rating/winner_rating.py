import numpy as np
import networkx as nx

from dfg_rating.model.network.base_network import BaseNetwork, TeamId, base_edge_filter
from dfg_rating.model.rating.base_rating import BaseRating, get_rounds


class WinnerRating(BaseRating):
    """Winner dummy rating adding 1 to the winner team rating.
    """
    def __init__(self, **kwargs):
        super().__init__('basic-winner', **kwargs)

    def get_all_ratings(self, network: BaseNetwork, edge_filter=None):
        edge_filter = edge_filter or base_edge_filter
        n_teams = len(network.data)
        games = network.data.edges(keys=True, data=True)
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
                1 if data['winner'] == 'away'
                else 0.5 if data['winner'] == 'draw'
                else 0
            )
            ratings[home_team][data['round'] + 1] = ratings[home_team][data['round']] + (
                1 if data['winner'] == 'home'
                else 0.5 if data['winner'] == 'draw'
                else 0
            )

        return ratings

    def get_ratings(self, network: BaseNetwork, team_id: [TeamId], edge_filter=None):
        edge_filter = edge_filter or base_edge_filter
        home_games = list(network.data.in_edges(team_id, keys=True, data=True))
        away_games = list(network.data.out_edges(team_id, keys=True, data=True))
        n_rounds = len(get_rounds(home_games + away_games))
        ratings = np.zeros([len(team_id), n_rounds + 1])
        for away_team, home_team, match_key, data in sorted(filter(edge_filter, home_games + away_games), key=lambda x: x[3]['round']):
            if away_team in team_id:
                ratings[away_team][data['round'] + 1] = ratings[away_team][data['round']] + 1 if data['winner'] == 'away' \
                    else 0.5 if data['winner'] == 'draw' \
                    else 0
            if home_team in team_id:
                ratings[home_team][data['round'] + 1] = ratings[home_team][data['round']] + 1 if data['winner'] == 'home' \
                    else 0.5 if data['winner'] == 'draw' \
                    else 0

        return ratings


if __name__ == '__main__':
    pass
