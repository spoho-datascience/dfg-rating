import numpy as np

from dfg_rating.model.network.base_network import BaseNetwork, TeamId, base_edge_filter, get_seasons
from dfg_rating.model.rating.base_rating import BaseRating, get_rounds, get_rounds_per_season


class ELORating(BaseRating):

    def __init__(self, **kwargs):
        super().__init__('elo', **kwargs)
        elo_trained = kwargs.get("trained", False)
        self.props = {}
        self.rating_name = kwargs.get('rating_name', 'elo_rating')
        if elo_trained:
            self.settings = {
                "c": kwargs.get("param_c", 10.0),
                "d": kwargs.get("param_d", 400.0),
                "k": kwargs.get("param_k", 14.0),
                "w": kwargs.get("param_w", 80)
            }

    def init_ratings(self, team, season, n, ratings):
        if self.seasons[season] == 0:
            """First season on the simulation, new starting point"""
            starting_point = self.rating_mean
        elif season == 0:
            """First season in the ratings computation but not in the network. Reading previous season"""
            starting_point = n.data.nodes[team].get('ratings', {}).get(self.rating_name, {}).get(
                self.seasons[season] - 1, [self.rating_mean]
            )[-1]
        else:
            """New season for the ratings. Getting previous rating"""
            starting_point = ratings[team][season * (self.rounds_per_season + 1)]
        return starting_point

    def init_season_ratings(self, season, n, ratings):
        init_position = season * (self.rounds_per_season + 2)
        for team in n.data.nodes:
            ratings[team, init_position] = self.init_ratings(team, season, n, ratings)

    def compute_expected_values(self, home_value, away_value):
        expected_home = 1.0 / (1.0 + (self.settings['c'] ** ((away_value - home_value - self.settings['w']) / self.settings['d'])))
        return expected_home, 1 - expected_home

    def compute_scores(self, result):
        home_score = 1.0 if result == 'home' else 0.5 if result == 'draw' else 0.0
        return home_score, 1 - home_score

    def update_elo(self, current, score, expected):
        return current + (self.settings['k'] * (score - expected))

    def end_season_ratings(self, season, network, ratings):
        end_position = (season + 1) * (self.rounds_per_season + 2) - 1
        for team in network.data.nodes:
            ratings[team, end_position] = ratings[team, end_position - 1]

    def get_all_ratings(self, n: BaseNetwork, edge_filter=None):
        edge_filter = edge_filter or base_edge_filter
        n_teams = n.n_teams
        games = n.data.edges(keys=True, data=True)
        filtered_games = [(away, home, key, data) for away, home, key, data in filter(edge_filter, games)]
        n_rounds = len(get_rounds(filtered_games))
        self.seasons = list(get_seasons(filtered_games))
        n_seasons = len(self.seasons)
        self.rounds_per_season = len(get_rounds_per_season(filtered_games))
        ratings = np.zeros([n_teams, (n_rounds + 2) * n_seasons])
        for current_season in range(n_seasons):
            # Init of values for all the ratings, with previous season or with nothing.
            self.init_season_ratings(current_season, n, ratings)
            for r in range(self.rounds_per_season):
                def round_filter(edge):
                    return edge[3]['round'] == r

                teams_playing = []
                for away_team, home_team, match_key, match_data in filter(round_filter, filtered_games):
                    if match_data.get('state', 'active') == 'active':
                        teams_playing += [away_team, home_team]
                        current_round = match_data['round']
                        current_position = (current_season * (self.rounds_per_season + 2)) + (current_round + 1)
                        home_expected, away_expected = self.compute_expected_values(
                            ratings[home_team, current_position - 1],
                            ratings[away_team, current_position - 1]
                        )
                        home_score, away_score = self.compute_scores(match_data['winner'])
                        ratings[away_team, current_position] = self.update_elo(
                            ratings[away_team, current_position - 1],
                            away_score,
                            away_expected
                        )
                        ratings[home_team, current_position] = self.update_elo(
                            ratings[home_team, current_position - 1],
                            home_score,
                            home_expected
                        )
                # Dealing with teams not playing
                for team in n.data.nodes:
                    if team not in teams_playing:
                        rating_pointer = (current_season * (self.rounds_per_season + 2)) + (r + 1)
                        ratings[team, rating_pointer] = ratings[team, rating_pointer - 1]
                self.end_season_ratings(current_season, n, ratings)
        return ratings, self.props

    def get_ratings(self, n: BaseNetwork, t: [TeamId], edge_filter=None):
        pass
