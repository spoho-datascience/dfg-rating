from operator import indexOf

import numpy as np

from dfg_rating.model.network.base_network import BaseNetwork, TeamId, base_edge_filter
from dfg_rating.model.rating.base_rating import BaseRating, get_rounds, get_seasons, get_rounds_per_season


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
        n_teams = n.n_teams
        games = n.data.edges(keys=True, data=True)
        filtered_games = [(away, home, key, data) for away, home, key, data in filter(edge_filter, games)]
        n_rounds = len(get_rounds(filtered_games))
        self.seasons = list(get_seasons(filtered_games))
        n_seasons = len(self.seasons)
        self.rounds_per_season = len(get_rounds_per_season(filtered_games))
        ratings = np.zeros([n_teams, n_rounds + (2 * n_seasons)])
        agg = {}
        current_season = -1
        for away_team, home_team, match_key, match_data in sorted(filtered_games,
                                                                  key=lambda edge: edge[3]['round']):
            if away_team not in agg:
                agg[away_team] = {
                    'current_season': -1,
                    'last_day': 0
                }
            if home_team not in agg:
                agg[home_team] = {
                    'current_season': -1,
                    'last_day': 0
                }
            if agg[home_team]['current_season'] != match_data.get('season', 0):
                current_season = match_data.get('season', 0)
                agg[home_team]['current_season'] = current_season
                ratings[home_team, (current_season - self.seasons[0]) * self.rounds_per_season] = \
                    self.init_ratings(agg, home_team, match_data, current_season, n, ratings)
            if agg[away_team]['current_season'] != match_data.get('season', 0):
                current_season = match_data.get('season', 0)
                agg[away_team]['current_season'] = current_season
                ratings[away_team, (current_season - self.seasons[0]) * self.rounds_per_season] = \
                    self.init_ratings(agg, away_team, match_data, current_season, n, ratings)
            ratings[away_team][(match_data['round'] + 1) + ((current_season - self.seasons[0]) * self.rounds_per_season)] = \
                ratings[away_team][(match_data['round']) + ((current_season - self.seasons[0]) * self.rounds_per_season)] + self.new_rating_value(agg, away_team, match_data)
            ratings[home_team][(match_data['round'] + 1) + ((current_season - self.seasons[0]) * self.rounds_per_season)] = \
                ratings[home_team][(match_data['round']) + ((current_season - self.seasons[0]) * self.rounds_per_season)] + self.new_rating_value(agg, home_team, match_data)
            if ((match_data['round'] + 2) % (self.rounds_per_season + 1)) == 0:
                ratings[home_team][(match_data['round'] + 2) + ((current_season - self.seasons[0]) * self.rounds_per_season)] = \
                    ratings[home_team][(match_data['round'] + 1) + ((current_season - self.seasons[0]) * self.rounds_per_season)]
                ratings[away_team][(match_data['round'] + 2) + ((current_season - self.seasons[0]) * self.rounds_per_season)] = \
                    ratings[away_team][(match_data['round'] + 1) + ((current_season - self.seasons[0]) * self.rounds_per_season)]

        return ratings, self.props

    def init_ratings(self, agg, team, match_data, current_season, n, ratings) -> float:
        agg[team]['trend'] = self.trend.get()[0]
        if current_season == 0:
            starting_point = self.starting_point.get()[0]
        elif current_season == self.seasons[0]:
            starting_point = self.apply_season_change(
                last_season_rating=n.data.nodes[team].get('ratings', {}).get(self.rating_name, {}).get(
                    current_season - 1, self.starting_point.get()
                )[-1]
            )
        else:
            starting_point = self.apply_season_change(
                last_season_rating=ratings[team][(current_season * self.rounds_per_season) - 1]
            )
        self.props.setdefault(team, {}).setdefault('starting_points', []).append(starting_point)
        self.props.setdefault(team, {}).setdefault('trends', []).append(agg[team]['trend'])
        return starting_point

    def apply_season_change(self, last_season_rating):
        return last_season_rating + self.season_delta.get()[0]

    def new_rating_value(self, agg, team, match_data):
        delta_days = match_data['day'] - agg[team]['last_day']
        agg[team]['last_day'] = match_data['day']
        total_delta = sum(self.delta.get(delta_days))
        round_ranking = agg[team]['trend'] * delta_days

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
