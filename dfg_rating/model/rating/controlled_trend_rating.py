from operator import indexOf

import numpy as np

from dfg_rating.model.network.base_network import BaseNetwork, TeamId, base_edge_filter
from dfg_rating.model.rating.base_rating import BaseRating, get_rounds


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
        return self.distribution_method(**self.distribution_arguments)


class ControlledTrendRating(BaseRating):

    def __init__(self, **kwargs):
        super().__init__('controlled-trend', **kwargs)
        self.starting_point: ControlledRandomFunction = kwargs['starting_point']
        self.delta: ControlledRandomFunction = kwargs['delta']
        self.trend: ControlledRandomFunction = kwargs['trend']
        self.trend_length: ControlledRandomFunction = kwargs.get('trend_length', 'season')
        self.season_delta: ControlledRandomFunction = kwargs['season_delta']

    def get_all_ratings(self, n: BaseNetwork, edge_filter=None):
        edge_filter = edge_filter or base_edge_filter
        n_teams = n.n_teams
        games = n.data.edges(keys=True, data=True)
        n_rounds = len(get_rounds(games))
        ratings = np.zeros([n_teams, n_rounds + 1])
        ratings[:, 0] = self.starting_point.get(n_teams)
        current_season = 0
        agg = {}
        for away_team, home_team, match_key, match_data in sorted(filter(edge_filter, games),
                                                                  key=lambda edge: edge[3]['round']):
            if match_data.get('season', 0) != current_season:
                print("New season")
                current_season = match_data['season']
                agg = {}

            ratings[away_team][match_data['round'] + 1] = ratings[away_team][0] + self.new_rating_value(agg, away_team,
                                                                                                        match_data)
            ratings[home_team][match_data['round'] + 1] = ratings[home_team][0] + self.new_rating_value(agg, home_team,
                                                                                                        match_data)
        return ratings

    def new_rating_value(self, agg, team, match_data):
        if team not in agg:
            agg[team] = {
                'trend': self.trend.get()[0],
                'last_day': 0
            }
        total_delta = sum(self.delta.get(match_data['day'] - agg[team]['last_day']))
        round_ranking = agg[team]['trend'] * float(match_data['round'] + 1)

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
        for away_team, home_team, match_key, match_data in sorted(filter(edge_filter, home_games + away_games), key=lambda x: x[3]['day']):
            if match_data.get('season', 0) != current_season:
                print("New season")
                current_season = match_data['season']
                agg = {}

            if home_team in t:
                i_home_team = indexOf(t, home_team)
                ratings[i_home_team][match_data['round'] + 1] = self.new_rating_value(agg, home_team, match_data)
            if away_team in t:
                i_away_team = indexOf(t, away_team)
                ratings[i_away_team][match_data['round'] + 1] = self.new_rating_value(agg, away_team, match_data)
        return ratings

