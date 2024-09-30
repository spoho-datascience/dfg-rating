import itertools
from operator import indexOf
import time
import numpy as np
from tqdm import tqdm

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

    def get(self, array_length=1, as_list=True):
        self.distribution_arguments['size'] = array_length
        if as_list:
            return list(self.distribution_method(**self.distribution_arguments))
        else:
            return self.distribution_method(**self.distribution_arguments)


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

    def get_all_ratings(self, n: BaseNetwork, edge_filter=None, season=0):
        print(season, "current_season")
        edge_filter = edge_filter or base_edge_filter
        self.teams = [t for t in range(n.n_teams)]
        n_teams = len(self.teams)
        n_rounds, round_values = n.get_rounds()
        self.rounds_per_season = n_rounds
        ratings = np.zeros([n_teams, (n_rounds + 2)])
        relative_season = 0
        self.agg = {}
        self.init_season_ratings(season, n, ratings)
        ratings[:, 0] *= self.rating_mean / np.ndarray.mean(ratings[:, 0])
        games_by_round = {}
        for k, g in itertools.groupby(
                filter(edge_filter, n.data.edges(keys=True, data=True)), lambda x: x[3]['round']
        ):
            games_by_round.setdefault(k, []).append(next(g))

        for r in range(self.rounds_per_season):
            r_value = round_values[r]
            teams_playing = []
            current_position = (relative_season * (self.rounds_per_season + 2)) + (r + 1)
            for away_team, home_team, match_key, match_data in games_by_round.get(r, []):
                teams_playing += [away_team, home_team]
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
                    ratings[team_i, current_position] = ratings[team_i, current_position - 1]
            ratings[:, current_position] *= self.rating_mean / np.ndarray.mean(ratings[:, current_position])
        self.end_season_ratings(relative_season, n, ratings)

        return ratings, self.props
    
    def get_cluster_ratings(self, n: BaseNetwork, level=None, season=0):
        # edge_filter = edge_filter or base_edge_filter
        if n.rating_mode == 'keep':
            self.teams = getattr(n, f'teams_rating_{level}')
        elif n.rating_mode == 'mix' or n.rating_mode == 'interchange':
            self.teams = getattr(n, f'teams_{level}')
        t = self.teams
        games = [(u, v, key, data) for u, v, key, data in n.data.edges(t, keys=True, data=True) if data['season'] == season and data['competition_type'] == 'League' and u in t and v in t]
        n_rounds = len(get_rounds(games))
        ratings = np.zeros([len(t), n_rounds + 1])
        self.agg = {}
        self.init_season_cluster_ratings(season, n, ratings)
        for away_team, home_team, match_key, match_data in sorted(games,
                                                                  key=lambda x: x[3]['day']):
            # if match_data.get('season', 0) != current_season:
            #     current_season = match_data['season']
            #     agg = {}
            if home_team in t:
                i_home_team = indexOf(t, home_team)
                ratings[i_home_team][match_data['round'] + 1] = ratings[i_home_team][match_data['round']] + self.new_rating_value(home_team, match_data)
            if away_team in t:
                i_away_team = indexOf(t, away_team)
                ratings[i_away_team][match_data['round'] + 1] = ratings[i_away_team][match_data['round']] + self.new_rating_value(away_team, match_data)
        return ratings, self.props

    def init_season_cluster_ratings(self, season, n, ratings):
        init_position = 0
        for team_i, team in enumerate(self.teams):
            self.agg.setdefault(
                team, {}
            )['trend'] = self.trend.get()[0]
            self.props.setdefault(
                team, {}
            ).setdefault(
                'trends', []
            ).append(self.agg[team]['trend'])
            team_starting = self.init_cluster_ratings(team, season, n)
            self.props.setdefault(
                team, {}
            ).setdefault(
                'starting_points', []
            ).append(team_starting)
            ratings[team_i, init_position] = team_starting

    def init_season_ratings(self, season, n, ratings):
        init_position = 0
        for team_i, team in enumerate(self.teams):
            self.agg.setdefault(
                team, {}
            )['trend'] = self.trend.get()[0]
            self.props.setdefault(
                team, {}
            ).setdefault(
                'trends', []
            ).append(self.agg[team]['trend'])
            team_starting = self.init_ratings(team, season, n)
            self.props.setdefault(
                team, {}
            ).setdefault(
                'starting_points', []
            ).append(team_starting)
            ratings[team_i, init_position] = team_starting

    def init_cluster_ratings(self, team, current_season, n) -> float:
        if current_season == 0:
            """First season on the simulation, new starting point"""
            starting_point = self.starting_point.get()[0]
        else:
            """First season in the ratings computation but not in the network. Reading previous season"""
            rating_mode = n.rating_mode
            if rating_mode == 'keep':
                starting_point = n.data.nodes[team].get('ratings', {}).get(self.rating_name, {}).get(
                        current_season - 1, self.starting_point.get()
                    )[-1] + self.season_delta.get()[0]
            elif rating_mode == 'mix':
                last_season_level = n.teams_level[team][current_season - 1]
                current_season_level = n.teams_level[team][current_season]
                if last_season_level == current_season_level:
                    starting_point = n.data.nodes[team].get('ratings', {}).get(self.rating_name, {}).get(
                        current_season - 1, self.starting_point.get()
                    )[-1] + self.season_delta.get()[0]
                else:
                    # keep mean rating in a level the same
                    last_season_rating = n.data.nodes[team].get('ratings', {}).get(self.rating_name, {}).get(
                        current_season - 1, self.starting_point.get()
                    )[-1]
                    default_rating = self.starting_point.get()
                    mean_rating_last_level = n.get_mean_rating(self.rating_name, current_season - 1, last_season_level, default_rating)
                    mean_rating_current_level = n.get_mean_rating(self.rating_name, current_season - 1, level=current_season_level, default_rating=default_rating)
                    rating_diff = mean_rating_current_level - mean_rating_last_level
                    # rating_diff = getattr(n, f'true_rating_{last_season_level}').rating_mean - getattr(n, f'true_rating_{current_season_level}').rating_mean
                    starting_point = last_season_rating + rating_diff+ self.season_delta.get()[0]
            elif rating_mode == 'interchange':
                last_season_level = n.teams_level[team][current_season - 1]
                current_season_level = n.teams_level[team][current_season]
                
                team_in = [t for t, l in n.teams_level.items() if l[current_season - 1] == last_season_level and l[current_season] == current_season_level]
                team_out = [t for t, l in n.teams_level.items() if l[current_season] == last_season_level and l[current_season - 1] == current_season_level]

                mean_team_in = np.mean([(n.data.nodes[t].get('ratings', {}).get(self.rating_name, {}).get(
                        current_season - 1, self.starting_point.get())[-1]) for t in team_in])
                mean_team_out = np.mean([(n.data.nodes[t].get('ratings', {}).get(self.rating_name, {}).get(
                        current_season - 1, self.starting_point.get())[-1]) for t in team_out])
                
                team_last_rating = n.data.nodes[team].get('ratings', {}).get(self.rating_name, {}).get(
                        current_season - 1, self.starting_point.get())[-1]
                
                starting_point =  team_last_rating/mean_team_in * mean_team_out + self.season_delta.get()[0]
                
        return starting_point
    def init_ratings(self, team, current_season, n) -> float:
        if current_season == 0:
            # print("first season")
            """First season on the simulation, new starting point"""
            starting_point = self.starting_point.get()[0]
        else:
            """First season in the ratings computation but not in the network. Reading previous season"""
            previous_playing_teams = n.get_playing_teams(current_season - 1)
            default_rating = self.starting_point.get()
            if team not in previous_playing_teams.values():
                mean_rating = n.get_mean_rating(self.rating_name, current_season - 1, default_rating, relegated=True)
                starting_point = self.apply_season_change(
                    last_season_rating=mean_rating
                )
            else:
                starting_point = self.apply_season_change(
                    last_season_rating=
                    n.data.nodes[team].get('ratings', {}).get(self.rating_name, {}).get(
                        current_season - 1, self.starting_point.get()
                    )[-1]
                )
        return starting_point

    def end_season_ratings(self, season, network, ratings):
        end_position = (season + 1) * (self.rounds_per_season + 2) - 1
        for team_i, team in enumerate(self.teams):
            ratings[team_i, end_position] = ratings[team_i, end_position - 1]

    def apply_season_change(self, last_season_rating):
        additive_value = self.season_delta.get()[0]
        #print("last_season_rating", last_season_rating, "additive", additive_value)
        return last_season_rating + additive_value

    def new_rating_value(self, team, match_data):
        delta_days = match_data['day'] - self.agg[team].get('last_day', 0)
        self.agg[team]['last_day'] = match_data['day']
        total_delta = self.delta.get(delta_days, as_list=False).sum()
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
