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
                "k": kwargs.get("param_k", 14.0),
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
                starting_point = n.get_mean_rating(self.rating_name, seasons_available[season_i - 1], league, [self.rating_mean], relegated=True)
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
        end_position = (self.rounds_per_season + 2) - 1
        for team_i, team in enumerate(self.teams):
            ratings[team_i, end_position] = ratings[team_i, end_position - 1]

    def get_all_ratings(self, n: BaseNetwork, edge_filter=None, season=0, **params):
        league_teams_dict = defaultdict(list)
        edge_filter = edge_filter or base_edge_filter
        self.teams = list(n.data.nodes)
        n_teams = len(self.teams)
        n_rounds, round_values = n.get_rounds()
        self.rounds_per_season = n_rounds
        ratings = np.zeros([n_teams, (n_rounds + 2)])
        self.init_season_ratings(season, n, ratings)
        players_dict = {team: team_i for team_i, team in enumerate(self.teams)}
        games_by_round = {}
        for k, g in itertools.groupby(
                filter(edge_filter, n.data.edges(keys=True, data=True)), lambda x: x[3]['round']
        ):
            games_by_round.setdefault(k, []).append(next(g))
        for r in range(self.rounds_per_season):
            r_value = round_values[r]
            teams_playing = set(())
            for away_team, home_team, match_key, match_data in games_by_round.get(r_value, {}):
                if match_data.get('state', 'active') == 'active':
                    home_team_i = players_dict.get(home_team, home_team)
                    away_team_i = players_dict.get(away_team, away_team)
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
                                        team_i = players_dict.get(team, team)
                                        ratings[team_i, current_position] = self.update_elo(
                                            ratings[team_i, current_position - 1],
                                            home_score,  # Use home team's result to adjust all teams in its league
                                            home_expected,
                                            adjusted_k,
                                            match_data
                                        )
                                for team in away_league_teams:
                                    if team != away_team:
                                        team_i = players_dict.get(team, team)
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
                        team_i = players_dict.get(team, team)
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
        adjusted_k = self.settings['k'] * (1 + np.absolute(home_score - away_score))**self.settings['lam']
        return adjusted_k
    
class OddsELORating(ELORating):

    def __init__(self, **kwargs):
        self.home_odds_pointer = kwargs.get('home_odds_pointer', 'home_odds')
        self.draw_odds_pointer = kwargs.get('draw_odds_pointer', 'draw_odds')
        self.away_odds_pointer = kwargs.get('away_odds_pointer', 'away_odds')
        super().__init__(**kwargs)

    def compute_scores(self, match_data):
        overround = 1/match_data[self.home_odds_pointer] + 1/match_data[self.draw_odds_pointer] + 1/match_data[self.away_odds_pointer]
        home_pred = 1/match_data[self.home_odds_pointer]/overround
        draw_pred = 1/match_data[self.draw_odds_pointer]/overround
        home_score = home_pred + 0.5 * draw_pred
        away_score = 1 - home_score
        return home_score, away_score
    