import itertools
import time
from operator import indexOf
from collections import defaultdict

import numpy as np
from tqdm import tqdm

from dfg_rating.model.network.base_network import BaseNetwork, TeamId, base_edge_filter, get_seasons
from dfg_rating.model.rating.base_rating import BaseRating, get_rounds, get_rounds_per_season


class ELORating(BaseRating):

    def __init__(self, **kwargs):
        super().__init__('elo', **kwargs)
        self.elo_trained = kwargs.get("trained", False)
        self.props = {}
        self.rating_name = kwargs.get('rating_name', 'elo_rating')
        if self.elo_trained:
            self.settings = {
                "c": kwargs.get("param_c", 10.0),
                "d": kwargs.get("param_d", 400.0),
                "k": kwargs.get("param_k", 20.0),
                "w": kwargs.get("param_w", 80),
                "lam": kwargs.get("param_lam", 1.6),
                "league_average": kwargs.get("league_average", False),
                "param_adjust": kwargs.get("param_adjust", False),
                "split_k": kwargs.get("param_split_k", {}),
                "split_lam": kwargs.get("param_split_lam", {})
            }

    def init_ratings(self, team, season, n, league=None):
        seasons_available = n.get_seasons()
        season_i = indexOf(seasons_available, season)
        if season_i == 0:
            """First season on the simulation, new starting point"""
            starting_point = self.rating_mean
        else:
            """First season in the ratings computation but not in the network. Reading previous season"""
            previous_playing_teams = n.get_playing_teams(seasons_available[season_i - 1], league)
            if team not in previous_playing_teams.values():
                starting_point = n.get_mean_rating(self.rating_name, seasons_available[season_i - 1], league,
                                                   [self.rating_mean], relegated=True)
            else:
                starting_point = n.data.nodes[team].get('ratings', {}).get(self.rating_name, {}).get(
                    seasons_available[season_i - 1], [self.rating_mean]
                )[-1]
        return starting_point

    def init_season_ratings(self, season, n, ratings):
        init_position = 0
        # n.update_leagues_information()
        for team_i, team in enumerate(n.data.nodes):
            current_league = n.get_current_league(season, team)
            ratings[team_i, init_position] = self.init_ratings(team, season, n, current_league)

    def init_new_player_ratings(self):
        pass

    def compute_expected_values(self, home_value, away_value):
        expected_home = 1.0 / (
                1.0 + (self.settings['c'] ** ((away_value - home_value - self.settings['w']) / self.settings['d'])))
        return expected_home, 1 - expected_home

    def compute_scores(self, match_data):
        result = match_data['winner']
        home_score = 1.0 if result == 'home' else 0.5 if result == 'draw' else 0.0
        return home_score, 1 - home_score

    def get_adjusted_k(self, match_data):
        if self.settings["param_adjust"] is True:
            adjusted_k = self.settings['split_k'].get(match_data['competition'], None)
        else:
            adjusted_k = self.settings['k']
        return adjusted_k

    def update_elo(self, current, score, expected, adjusted_k, match_data):
        return current + (adjusted_k * (score - expected))

    def end_season_ratings(self, network, ratings):
        ratings[:, -1] = ratings[:, -2]

    def get_all_ratings(self, n: BaseNetwork, edge_filter=None, season=0, **params):
        league_teams_dict = defaultdict(list)
        edge_filter = edge_filter or base_edge_filter
        self.teams = list(n.data.nodes)
        n_teams = len(self.teams)
        n_rounds, round_values = n.get_rounds()
        self.rounds_per_season = n_rounds[season]
        ratings = np.zeros([n_teams, (n_rounds[season] + 2)])
        self.init_season_ratings(season, n, ratings)
        team_dict = {team: team_i for team_i, team in enumerate(self.teams)}
        games_by_round = {}
        for k, g in itertools.groupby(
                filter(edge_filter, n.data.edges(keys=True, data=True)), lambda x: x[3]['round']
        ):
            games_by_round.setdefault(k, []).extend(g)
        for r in range(self.rounds_per_season):
            r_value = round_values[season][r]
            teams_playing = set(())
            for away_team, home_team, match_key, match_data in games_by_round.get(r_value, {}):
                if match_data.get('state', 'active') == 'active':
                    home_team_i = team_dict.get(home_team, home_team)
                    away_team_i = team_dict.get(away_team, away_team)
                    teams_playing.update([away_team, home_team])
                    current_round = match_data['round']
                    current_position = r + 1
                    home_expected, away_expected = self.compute_expected_values(
                        ratings[home_team_i, current_position - 1],
                        ratings[away_team_i, current_position - 1]
                    )
                    home_score, away_score = self.compute_scores(match_data)
                    adjusted_k = self.get_adjusted_k(match_data)
                    ratings[away_team_i, current_position] = self.update_elo(
                        ratings[away_team_i, current_position - 1],
                        away_score,
                        away_expected,
                        adjusted_k,
                        match_data
                    )
                    ratings[home_team_i, current_position] = self.update_elo(
                        ratings[home_team_i, current_position - 1],
                        home_score,
                        home_expected,
                        adjusted_k,
                        match_data
                    )
                    if self.settings["league_average"] is True:
                        # Check for International or Cup match
                        if match_data['competition'] in ['International', 'Cup']:
                            home_league_id = match_data['home_team_league_id']
                            away_league_id = match_data['away_team_league_id']
                            if home_league_id != away_league_id:
                                # Get all teams in the respective leagues
                                home_league_teams = [team for team in self.teams if
                                                     n.data.nodes[team].get('league_id') == home_league_id]
                                away_league_teams = [team for team in self.teams if
                                                     n.data.nodes[team].get('league_id') == away_league_id]
                                # Apply the league-wide rating adjustments
                                for team in home_league_teams:
                                    if team != home_team:
                                        team_i = team_dict.get(team, team)
                                        ratings[team_i, current_position] = self.update_elo(
                                            ratings[team_i, current_position - 1],
                                            home_score,  # Use home team's result to adjust all teams in its league
                                            home_expected,
                                            adjusted_k,
                                            match_data
                                        )
                                for team in away_league_teams:
                                    if team != away_team:
                                        team_i = team_dict.get(team, team)
                                        ratings[team_i, current_position] = self.update_elo(
                                            ratings[team_i, current_position - 1],
                                            away_score,  # Use away team's result to adjust all teams in its league
                                            away_expected,
                                            adjusted_k,
                                            match_data
                                        )
                                teams_playing.update(home_league_teams, away_league_teams)
            # Dealing with teams not playing
            if len(teams_playing) != len(self.teams):
                for team in self.teams:
                    if team not in teams_playing:
                        team_i = team_dict.get(team, team)
                        rating_pointer = r + 1
                        ratings[team_i, rating_pointer] = ratings[team_i, rating_pointer - 1]
        self.end_season_ratings(n, ratings)
        return ratings, self.props

    def get_ratings(self, n: BaseNetwork, t: [TeamId], edge_filter=None):
        pass


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


class GoalsELORating(ELORating):

    def __init__(self, **kwargs):
        self.home_score_key = kwargs.get('home_score_key', 'home_score')
        self.away_score_key = kwargs.get('away_score_key', 'away_score')
        super().__init__(**kwargs)

    def get_adjusted_k(self, match_data):
        home_score = match_data[self.home_score_key]
        away_score = match_data[self.away_score_key]
        if self.settings["param_adjust"] is True:
            k = self.settings['split_k'].get(match_data['competition'], None)
            lam = self.settings["split_lam"].get(match_data['competition'], None)
            adjusted_k = k * (1 + np.absolute(home_score - away_score)) ** lam
        else:
            adjusted_k = self.settings['k'] * (1 + np.absolute(home_score - away_score)) ** self.settings['lam']
        return adjusted_k


class OddsELORating(ELORating):

    def __init__(self, **kwargs):
        self.home_odds_pointer = kwargs.get('home_odds_pointer', 'home_odds')
        self.draw_odds_pointer = kwargs.get('draw_odds_pointer', 'draw_odds')
        self.away_odds_pointer = kwargs.get('away_odds_pointer', 'away_odds')
        super().__init__(**kwargs)

    def compute_scores(self, match_data):
        overround = 1 / match_data[self.home_odds_pointer] + 1 / match_data[self.draw_odds_pointer] + 1 / match_data[
            self.away_odds_pointer]
        home_pred = 1 / match_data[self.home_odds_pointer] / overround
        draw_pred = 1 / match_data[self.draw_odds_pointer] / overround
        home_score = home_pred + 0.5 * draw_pred
        away_score = 1 - home_score
        return home_score, away_score


class PlayerELORating(ELORating):

    def __init__(self, **kwargs):
        self.home_score_key = kwargs.get('home_score_key', 'home_score')
        self.away_score_key = kwargs.get('away_score_key', 'away_score')
        self.use_odds = kwargs.get('use_odds', False)
        self.home_odds_pointer = kwargs.get('home_odds_pointer', 'home_odds')
        self.draw_odds_pointer = kwargs.get('draw_odds_pointer', 'draw_odds')
        self.away_odds_pointer = kwargs.get('away_odds_pointer', 'away_odds')
        self.match_weight = kwargs.get('match_weight', 1)
        self.debug_trace_drift = kwargs.get('debug_trace_drift', False)
        super().__init__(**kwargs)

    def init_player_ratings(self, player, season, n):
        seasons_available = n.get_seasons()
        season_i = indexOf(seasons_available, season)
        if season_i != 0:
            """Reading previous season"""
            starting_point = n.player_info[player].get('ratings', {}).get(self.rating_name, {}).get(
                seasons_available[season_i - 1], [self.rating_mean]
            )[-1]
        else:
            starting_point = np.nan
        return starting_point

    def init_season_player_ratings(self, season, n, ratings):
        init_position = 0
        # n.update_leagues_information()
        for player_i in n.player_info:
            ratings[player_i - 1, init_position] = self.init_player_ratings(player_i, season, n)

    def init_new_player_ratings(self, player_ratings, last_team_rating):
        valid_ratings = [r for r in player_ratings if not np.isnan(r)]
        player_ratings = np.array(player_ratings, dtype=float)
        if len(valid_ratings) <= len(player_ratings) / 2:
            filled_ratings = np.where(
                np.isnan(player_ratings),
                last_team_rating,
                player_ratings
            )
        else:
            filler = np.mean(valid_ratings)
            filled_ratings = np.where(
                np.isnan(player_ratings),
                filler,
                player_ratings
            )
        return filled_ratings

    def compute_scores(self, match_data):
        if not self.use_odds:
            result = match_data['winner']
            home_score = 1.0 if result == 'home' else 0.5 if result == 'draw' else 0.0
            away_score = 1 - home_score
        else:
            overround = 1 / match_data[self.home_odds_pointer] + 1 / match_data[self.draw_odds_pointer] + 1 / \
                        match_data[
                            self.away_odds_pointer]
            home_pred = 1 / match_data[self.home_odds_pointer] / overround
            draw_pred = 1 / match_data[self.draw_odds_pointer] / overround
            home_score = home_pred + 0.5 * draw_pred
            away_score = 1 - home_score
        return home_score, away_score

    def compute_player_expected_values(self, player_value, opposition_value, side):
        if side == 'home':
            home_advantage = self.settings['w']
        else:
            home_advantage = - self.settings['w']
        expected_player = 1.0 / (
                1.0 + (self.settings['c'] ** (
                (opposition_value - player_value - home_advantage) / self.settings['d'])))
        return expected_player

    def compute_player_scores(self, goal_difference):
        player_score = 1.0 if goal_difference > 0 else 0.5 if goal_difference == 0 else 0.0
        return player_score

    def update_player_elo(self, current, score, expected, change_team, minutes_played, max_minutes, k=40, q=1, weight=1,
                          goal_diff=0):
        change_player = self.get_player_rating_change(score, expected, minutes_played, max_minutes, goal_diff)
        updated_rating = current + k * weight * (
                q * change_player + (1 - q) * change_team * (minutes_played / max_minutes))
        return updated_rating

    def get_player_rating_change(self, score, expected, minutes_played, max_minutes, goal_diff):
        if goal_diff == 0:
            rating_change_player = (score - expected) * (minutes_played / max_minutes)
        else:
            rating_change_player = (score - expected) * np.cbrt(abs(goal_diff))
        return rating_change_player

    def get_team_rating_change(self, score, expected, goal_diff):
        if goal_diff == 0:
            rating_change_team = (score - expected)
        else:
            rating_change_team = (score - expected) * np.cbrt(abs(goal_diff))
        return rating_change_team

    def get_team_rating(self, player_ratings, minutes):
        return sum(x * y for x, y in zip(player_ratings, minutes)) / sum(minutes)

    def update_elo(self, current, rating_change, w=1, adjusted_k=20):
        return current + w * (adjusted_k * rating_change)

    def get_adjusted_params(self, n, side, team):
        active_players = set(side['id'])
        inactive_players = (
                self.players_by_team[team]
                - active_players
        )
        # k ranging between 24 and 40, q between 0.5 and 1
        for player_id in active_players:
            n.player_info[player_id]["k"] = max(
                130,
                n.player_info[player_id]["k"] - 0.25
            )
            n.player_info[player_id]["q"] = max(
                0.5,
                n.player_info[player_id]["q"] - 0.025
            )
            n.player_info[player_id]["played"] = True
        for player_id in inactive_players:
            n.player_info[player_id]["k"] = min(
                170,
                n.player_info[player_id]["k"] + 0.5
            )
            n.player_info[player_id]["q"] = min(
                1.0,
                n.player_info[player_id]["q"] + 0.025
            )
            n.player_info[player_id]["played"] = False

    def get_all_ratings(self, n: BaseNetwork, edge_filter=None, season=0, **params):
        edge_filter = edge_filter or base_edge_filter
        self.teams = list(n.data.nodes)
        self.players = list(n.player_info.keys())
        self.players_by_team = {}
        n_teams = len(self.teams)
        n_players = len(self.players)
        n_rounds, round_values = n.get_rounds()
        self.rounds_per_season = n_rounds[season]
        team_ratings = np.zeros([n_teams, (n_rounds[season] + 2)])
        #player_ratings = np.full((n_players, n_rounds[season] + 2), np.nan, dtype=float)
        self.init_season_ratings(season, n, team_ratings)
        #self.init_season_player_ratings(season, n, player_ratings)
        team_dict = {team: team_i for team_i, team in enumerate(self.teams)}
        #player_dict = {player: player_i for player_i, player in enumerate(self.players)}
        games_by_round = {}
        adjusted_k = self.settings['k']
        for k, g in itertools.groupby(
                filter(edge_filter, n.data.edges(keys=True, data=True)), lambda x: x[3]['round']
        ):
            games_by_round.setdefault(k, []).extend(g)
        for r in range(self.rounds_per_season):
            r_value = round_values[season][r]
            teams_playing = set(())
            players_playing = set(())
            for away_team, home_team, match_key, match_data in games_by_round.get(r_value, {}):
                if match_data.get('state', 'active') == 'active':
                    match_data['home_player_ratings'] = []
                    match_data['away_player_ratings'] = []
                    match_data['home_player_prev_ratings'] = []
                    match_data['away_player_prev_ratings'] = []
                    n.data[away_team][home_team][match_key]['home_player_ratings'] = []
                    n.data[away_team][home_team][match_key]['away_player_ratings'] = []
                    n.data[away_team][home_team][match_key]['home_player_prev_ratings'] = []
                    n.data[away_team][home_team][match_key]['away_player_prev_ratings'] = []
                    home_team_rating = []
                    away_team_rating = []
                    home_player_ratings = []
                    away_player_ratings = []
                    home_team_i = team_dict.get(home_team, home_team)
                    away_team_i = team_dict.get(away_team, away_team)
                    teams_playing.update([away_team, home_team])
                    players_playing.update(match_data['lineup']['home']['id'])
                    players_playing.update(match_data['lineup']['away']['id'])
                    current_round = match_data['round']
                    current_position = r + 1
                    home_actual, away_actual = self.compute_scores(match_data)
                    home_goal_diff = match_data[self.home_score_key] - match_data[self.away_score_key]
                    away_goal_diff = match_data[self.away_score_key] - match_data[self.home_score_key]
                    last_home_team_rating = float(team_ratings[home_team_i, current_position - 1])
                    last_away_team_rating = float(team_ratings[away_team_i, current_position - 1])
                    home_expected, away_expected = self.compute_expected_values(
                        last_home_team_rating,
                        last_away_team_rating
                    )
                    home_team_rating_change = self.get_team_rating_change(home_actual, home_expected, goal_diff=0)
                    team_ratings[home_team_i, current_position] = self.update_elo(
                        last_home_team_rating,
                        home_team_rating_change,
                        self.match_weight,
                        adjusted_k,
                    )
                    away_team_rating_change = self.get_team_rating_change(away_actual, away_expected, goal_diff=0)
                    if abs(home_team_rating_change+away_team_rating_change) > 1e-6:
                        print(f"season:", season)
                        print(f"date:", match_data['date'])
                        print(f"home team:", match_data['home_team'], "away team:", match_data['away_team'])
                        print(f"home team change:", home_team_rating_change)
                        print(f"away team change:", away_team_rating_change)
                    team_ratings[away_team_i, current_position] = self.update_elo(
                        last_away_team_rating,
                        away_team_rating_change,
                        self.match_weight,
                        adjusted_k,
                    )
                    if len(match_data['lineup']['home']['id']) == 0:
                        continue
                    for side_name in match_data['lineup'].keys():
                        side = match_data['lineup'][side_name]
                        player_ratings = [
                            float(n.player_info[p]['rating'])
                            for p in side['id']
                        ]
                        if side_name == 'home':
                            home_player_ratings = self.init_new_player_ratings(player_ratings,
                                                                               last_home_team_rating)
                            home_player_ratings = [float(x) for x in home_player_ratings]
                            n.data[away_team][home_team][match_key]['home_player_prev_ratings'] = list(
                                home_player_ratings)
                            home_team_rating = self.get_team_rating(home_player_ratings, side['minutes'])
                        elif side_name == 'away':
                            away_player_ratings = self.init_new_player_ratings(player_ratings,
                                                                               last_away_team_rating)
                            away_player_ratings = [float(x) for x in away_player_ratings]
                            n.data[away_team][home_team][match_key]['away_player_prev_ratings'] = list(
                                away_player_ratings)
                            away_team_rating = self.get_team_rating(away_player_ratings, side['minutes'])
                    home_expected, away_expected = self.compute_expected_values(
                        home_team_rating,
                        away_team_rating
                    )
                    for side_name in match_data['lineup'].keys():
                        side = match_data['lineup'][side_name]
                        if side_name == 'home':
                            team = home_team
                            opponent_rating = away_team_rating
                            player_ratings = home_player_ratings
                            team_rating_change = self.get_team_rating_change(home_actual, home_expected, home_goal_diff)
                        elif side_name == 'away':
                            team = away_team
                            opponent_rating = home_team_rating
                            player_ratings = away_player_ratings
                            team_rating_change = self.get_team_rating_change(away_actual, away_expected, away_goal_diff)
                        else:
                            opponent_rating = self.rating_mean
                            player_ratings = self.rating_mean
                            team_rating_change = 0
                            team = -1
                        if team not in self.players_by_team:
                            self.players_by_team[team] = set(side['id'])
                        else:
                            self.players_by_team[team].update(side['id'])
                        max_minutes = max(side['minutes'])
                        for idx, player in enumerate(side['id']):
                            n.player_info[side['id'][idx]]['last_team'] = n.player_info[side['id'][idx]]['current_team']
                            n.player_info[side['id'][idx]]['current_team'] = team
                            old_team = n.player_info[side['id'][idx]]["last_team"]
                            if old_team is not None:
                                if old_team != team:
                                    if old_team in self.players_by_team:
                                        self.players_by_team[old_team].discard(side['id'][idx])
                                        # initial k = 40, q = 1
                                    n.player_info[side['id'][idx]]["k"] = 150
                                    n.player_info[side['id'][idx]]["q"] = 1
                            actual = self.compute_player_scores(side['goal_difference'][idx])
                            rating = player_ratings[idx]
                            expected = self.compute_player_expected_values(rating, opponent_rating, side_name)
                            updated_rating = self.update_player_elo(rating,
                                                                    actual,
                                                                    expected,
                                                                    team_rating_change,
                                                                    side['minutes'][idx],
                                                                    max_minutes,
                                                                    n.player_info[side['id'][idx]]['k'],
                                                                    n.player_info[side['id'][idx]]['q'],
                                                                    self.match_weight,
                                                                    side['goal_difference'][idx])
                            #player_ratings[player_dict[side['id'][idx]], current_position] = updated_rating
                            n.player_info[side['id'][idx]]['rating'] = float(updated_rating)
                            if side_name == "home":
                                match_data['home_player_ratings'].append(float(updated_rating))
                            elif side_name == "away":
                                match_data['away_player_ratings'].append(float(updated_rating))
                        self.get_adjusted_params(n, side, team)
                    n.data[away_team][home_team][match_key]['home_player_ratings'] = match_data['home_player_ratings']
                    n.data[away_team][home_team][match_key]['away_player_ratings'] = match_data['away_player_ratings']

            # Dealing with teams not playing
            missing_teams = set(self.teams) - set(teams_playing)
            if missing_teams:
                team_idx = [team_dict[t] for t in missing_teams]
                team_ratings[team_idx, r + 1] = (
                    team_ratings[team_idx, r]
                )
            #missing_players = set(self.players) - set(players_playing)
            #if missing_players:
            #    player_idx = [player_dict[t] for t in missing_players]
            #    player_ratings[player_idx, r + 1] = (
            #        player_ratings[player_idx, r]
            #    )
        self.end_season_ratings(n, team_ratings)
        #self.end_season_ratings(n, player_ratings)
        return team_ratings, self.props