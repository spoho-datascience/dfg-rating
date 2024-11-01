import itertools
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
    
    def get_ratings(self, n: BaseNetwork, level=None, season=0):
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
        self.init_season_ratings(season, n, ratings)
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

    def get_all_ratings(self):
        pass

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

    def init_ratings(self, team, current_season, n) -> float:
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


class LeagueRating(BaseRating):
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
    
    def get_all_ratings(self):
        pass
    
    def get_ratings(self, league_network: BaseNetwork, team: [TeamId], season=0, level=0):
        season_games = [(u, v, key, data) for u, v, key, data in league_network.data.edges(keys=True, data=True) if u in team and v in team and data['season'] == season and data['competition_type']=='League']

        n_rounds = len(get_rounds(season_games))
        # n_rounds, round_value = league_network.get_rounds()
        ratings = np.zeros([len(team), n_rounds + 1])
        for away_team, home_team, match_key, data in sorted(season_games, key=lambda x: x[3]['day']):
            if home_team in team:
                i_home_team = indexOf(team, home_team)
                ratings[i_home_team][data['round'] + 1] = ( # just get the value of the round
                    self.points_system['win'] if data['winner'] == 'home'
                    else self.points_system['draw'] if data['winner'] == 'draw'
                    else self.points_system['lose']
                )
            if away_team in team:
                i_away_team = indexOf(team, away_team)
                ratings[i_away_team][data['round'] + 1] = (
                    self.points_system['win'] if data['winner'] == 'away'
                    else self.points_system['draw'] if data['winner'] == 'draw'
                    else self.points_system['lose']
                )
        # accumulate ratings by round
        ratings = np.cumsum(ratings, axis=1)
        return ratings, self.points_system


class ELORating(BaseRating):

    def __init__(self, **kwargs):
        super().__init__('elo', **kwargs)
        self.elo_trained = kwargs.get("trained", False)
        self.props = {}
        self.rating_name = kwargs.get('rating_name', 'elo_rating')
        self.rating_mode = kwargs.get('rating_mode', 'keep')
        if self.elo_trained:
            self.settings = {
                "c": kwargs.get("param_c", 10.0),
                "d": kwargs.get("param_d", 400.0),
                "k": kwargs.get("param_k", 14.0),
                "w": kwargs.get("param_w", 80)
            }

    def init_ratings(self, team, season, n):
        seasons_available = n.get_seasons()
        season_i = indexOf(seasons_available, season)
        if season_i == 0:
            """First season on the simulation, new starting point"""
            starting_point = self.rating_mean
        else:
            # """First season in the ratings computation but not in the network. Reading previous season"""
            previous_playing_teams = n.get_playing_teams(seasons_available[season_i - 1], league)
            if team not in previous_playing_teams.values():
                starting_point = n.get_mean_rating(self.rating_name, seasons_available[season_i - 1], league, [self.rating_mean], relegated=True)
            else:
                starting_point = n.data.nodes[team].get('ratings', {}).get(self.rating_name, {}).get(
                    seasons_available[season_i - 1], [self.rating_mean]
                )[-1]
        return starting_point

    def init_season_ratings(self, season, teams, n, ratings):
        init_position = 0
        # n.update_leagues_information()
        for team_i, team in enumerate(teams):
            # current_league = n.get_current_league(season, team)
            ratings[team_i, init_position] = self.init_ratings(team, season, n)

    def compute_expected_values(self, home_value, away_value):
        expected_home = 1.0 / (
            1.0 + (self.settings['c'] ** ((away_value - home_value - self.settings['w']) / self.settings['d'])))
        return expected_home, 1 - expected_home

    def compute_scores(self, result):
        home_score = 1.0 if result == 'home' else 0.5 if result == 'draw' else 0.0
        return home_score, 1 - home_score

    def update_elo(self, current, score, expected, match_data):
        return current + (self.settings['k'] * (score - expected))

    def end_season_ratings(self, network, ratings):
        end_position = (self.rounds_per_season + 2) - 1
        for team_i, team in enumerate(self.teams):
            ratings[team_i, end_position] = ratings[team_i, end_position - 1]

    def get_all_ratings(self, n: BaseNetwork, edge_filter=None, season=0, **params):
        edge_filter = edge_filter or base_edge_filter
        self.teams = [].append(list(nation.data.nodes) for nation in n.countries_leagues.values())
        n_teams = len(self.teams)
        self.rounds_per_season = 365
        ratings = np.zeros([n_teams, (365 + 2)])
        self.init_season_ratings(season, n, ratings)
        players_dict = {team: team_i for team_i, team in enumerate(self.teams)}
        games = sorted(
            (filter(edge_filter, nation.data.edges(keys=True, data=True)) for nation in n.countries_leagues.values()),
            key=lambda x: x[3]['day']
        )
        for match in games:
            away_team, home_team, match_key, match_data = match
            current_day = match_data['day']
            home_team_i = players_dict.get(home_team, home_team)
            away_team_i = players_dict.get(away_team, away_team)
            home_expected, away_expected = self.compute_expected_values(
                ratings[home_team_i, current_day - 1],
                ratings[away_team_i, current_day - 1]
            )
            home_score, away_score = self.compute_scores(match_data['winner'])
            ratings[away_team_i, current_day] = self.update_elo(
                ratings[away_team_i, current_day - 1],
                away_score,
                away_expected,
                match_data
            )
            ratings[home_team_i, current_day] = self.update_elo(
                ratings[home_team_i, current_day - 1],
                home_score,
                home_expected,
                match_data
            )
            for team in self.teams:
                if team not in [home_team, away_team]:
                    team_i = players_dict[team]
                    ratings[team_i, current_day] = ratings[team_i, current_day - 1]
        
        self.end_season_ratings(n, ratings)
        return ratings, self.props

    def get_ratings(self, n: BaseNetwork, level=None, season=0):
        self.teams = getattr(n, f'teams_{level}')
        games = [(u, v, key, data) for u, v, key, data in n.data.edges(keys=True, data=True) if data['season'] == season and data['competition_type'] == 'League' and u in self.teams and v in self.teams]
        n_rounds = len(get_rounds(games))
        ratings = np.zeros([len(self.teams), n_rounds + 1])
        self.init_season_ratings(season, n, ratings)
        players_dict = {team: team_i for team_i, team in enumerate(self.teams)}


class SplitELORating(ELORating):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.elo_trained:
            self.settings["split_k"] = kwargs.get("param_split_k", {})

    def update_elo(self, current, score, expected, match_data):
        if 'split_k_group' in match_data:
            k_factor = self.settings.get('split_k', {}).get(match_data['split_k_group'], None)
            if k_factor is not None:
                return current + (k_factor * (score - expected))
        return current + (self.settings['k'] * (score - expected))