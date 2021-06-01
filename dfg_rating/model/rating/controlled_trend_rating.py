from operator import indexOf

import numpy as np

from dfg_rating.model.network.base_network import BaseNetwork, TeamId, base_edge_filter, get_seasons
from dfg_rating.model.rating.base_rating import BaseRating, get_rounds, get_rounds_per_season


class ControlledRandomFunction:

    def __init__(self, **kwargs):
        try:
            self.distribution_method = getattr(np.random.default_rng(), kwargs['distribution'])
            kwargs.pop('distribution', None)
            self.distribution_arguments = kwargs
        except AttributeError as attr:
            print("Distribution method not available")
            raise attr

    def get(self, array_length=1):
        self.distribution_arguments['size'] = array_length
        return list(self.distribution_method(**self.distribution_arguments))


class ControlledTrendRating(BaseRating):

    def __init__(self, **kwargs):
        super().__init__('controlled-trend', **kwargs)
        self.starting_point: ControlledRandomFunction = kwargs['starting_point']
        self.delta: ControlledRandomFunction = kwargs['delta']
        self.trend: ControlledRandomFunction = kwargs['trend']
        self.trend_length: ControlledRandomFunction = kwargs.get('trend_length', 'season')
        self.season_delta: ControlledRandomFunction = kwargs['season_delta']
        self.props = {}
        self.rating_name = kwargs.get('rating_name', 'true_rating')

    def get_all_ratings(self, n: BaseNetwork, edge_filter=None):
        edge_filter = edge_filter or base_edge_filter
        self.teams = list(n.data.nodes)
        n_teams = len(self.teams)
        games = n.data.edges(keys=True, data=True)
        filtered_games = [(away, home, key, data) for away, home, key, data in filter(edge_filter, games)]
        n_rounds = len(get_rounds(filtered_games))
        self.seasons = list(get_seasons(filtered_games))
        n_seasons = len(self.seasons)
        self.rounds_per_season = len(get_rounds_per_season(filtered_games))
        # The ratings object is initialized with as many positions as number of rounds in the network
        # and 2 extra positions (begin, end) of the season.
        ratings = np.zeros([n_teams, (n_rounds + 2) * n_seasons])
        for current_season, season_name in enumerate(self.seasons):
            self.agg = {}
            self.init_season_ratings(current_season, season_name, n, ratings)
            for r in range(self.rounds_per_season):
                def round_filter(edge):
                    return edge[3]['round'] == r

                # Teams playing
                teams_playing = []
                for away_team, home_team, match_key, match_data in filter(round_filter, filtered_games):
                    teams_playing += [away_team, home_team]
                    current_round = match_data['round']
                    current_position = (current_season * (self.rounds_per_season + 2)) + (current_round + 1)
                    ratings[indexOf(self.teams, away_team), current_position] = ratings[
                                                                                    indexOf(self.teams,
                                                                                            away_team), current_position - 1
                                                                                ] + self.new_rating_value(away_team,
                                                                                                          match_data)
                    self.agg[away_team]['last_day'] = match_data['day']
                    ratings[indexOf(self.teams, home_team), current_position] = ratings[
                                                                                    indexOf(self.teams,
                                                                                            home_team), current_position - 1
                                                                                ] + self.new_rating_value(home_team,
                                                                                                          match_data)
                    self.agg[home_team]['last_day'] = match_data['day']
                # Dealing with teams not playing
                for team_i, team in enumerate(self.teams):
                    if team not in teams_playing:
                        rating_pointer = (current_season * (self.rounds_per_season + 2)) + (r + 1)
                        ratings[team_i, rating_pointer] = ratings[team_i, rating_pointer - 1]
            self.end_season_ratings(current_season, n, ratings)
        return ratings, self.props

    def init_season_ratings(self, season, season_name, n, ratings):
        init_position = season * (self.rounds_per_season + 2)
        for team_i, team in enumerate(self.teams):
            self.agg.setdefault(
                team, {}
            )['trend'] = self.trend.get()[0]
            self.props.setdefault(
                team, {}
            ).setdefault(
                'trends', []
            ).append(self.agg[team]['trend'])
            team_starting = self.init_ratings(team, season, season_name, n, ratings)
            self.props.setdefault(
                team, {}
            ).setdefault(
                'starting_points', []
            ).append(team_starting)
            ratings[team_i, init_position] = team_starting

    def init_ratings(self, team, current_season, season_name, n, ratings) -> float:
        if indexOf(self.seasons, season_name) == 0:
            """First season on the simulation, new starting point"""
            starting_point = self.starting_point.get()[0]
        elif current_season == 0:
            """First season in the ratings computation but not in the network. Reading previous season"""
            starting_point = self.apply_season_change(
                last_season_rating=
                n.data.nodes[indexOf(self.teams, team)].get('ratings', {}).get(self.rating_name, {}).get(
                    indexOf(self.seasons, season_name) - 1, self.starting_point.get()
                )[-1]
            )
        else:
            """New season for the ratings. Getting previous rating"""
            starting_point = self.apply_season_change(
                last_season_rating=ratings[indexOf(self.teams, team)][current_season * (self.rounds_per_season + 1)]
            )
        return starting_point

    def end_season_ratings(self, season, network, ratings):
        end_position = (season + 1) * (self.rounds_per_season + 2) - 1
        for team_i, team in enumerate(self.teams):
            ratings[team_i, end_position] = ratings[team_i, end_position - 1]

    def apply_season_change(self, last_season_rating):
        return last_season_rating + self.season_delta.get()[0]

    def new_rating_value(self, team, match_data):
        delta_days = match_data['day'] - self.agg[team].get('last_day', 0)
        self.agg[team]['last_day'] = match_data['day']
        total_delta = sum(self.delta.get(delta_days))
        round_ranking = self.agg[team]['trend'] * delta_days

        return round_ranking + total_delta

    def get_ratings(self, n: BaseNetwork, t: [TeamId], edge_filter=None):
        edge_filter = edge_filter or base_edge_filter
        home_games = list(n.data.in_edges(t, keys=True, data=True))
        away_games = list(n.data.out_edges(t, keys=True, data=True))
        n_rounds = len(get_rounds(home_games + away_games))
        ratings = np.zeros([len(t), n_rounds + 1])
        ratings[:, 0] = self.starting_point.get(len(t))
        agg = {}
        current_season = 0
        for away_team, home_team, match_key, match_data in sorted(filter(edge_filter, home_games + away_games),
                                                                  key=lambda x: x[3]['day']):
            if match_data.get('season', 0) != current_season:
                current_season = match_data['season']
                agg = {}

            if home_team in t:
                i_home_team = indexOf(t, home_team)
                ratings[i_home_team][match_data['round'] + 1] = self.new_rating_value(agg, home_team, match_data)
            if away_team in t:
                i_away_team = indexOf(t, away_team)
                ratings[i_away_team][match_data['round'] + 1] = self.new_rating_value(agg, away_team, match_data)
        return ratings, self.props
