from dfg_rating.model.bookmaker.base_bookmaker import BaseBookmaker
import numpy as np
import pandas as pd
import random
import networkx as nx
import numpy as np
from networkx import DiGraph
from dfg_rating.model.network.simple_network import RoundRobinNetwork
from dfg_rating.model.network.base_network import BaseNetwork
import math
import copy
from dfg_rating.model.forecast.true_forecast import LogFunctionForecast
# from dfg_rating.model.rating.controlled_trend_rating import ControlledTrendRating, ControlledRandomFunction
from dfg_rating.model.rating.multi_mode_rating import ControlledTrendRating, ControlledRandomFunction
from dfg_rating.model.rating.base_rating import BaseRating
# from dfg_rating.model.rating.ranking_rating import LeagueRating
from dfg_rating.model.rating.multi_mode_rating import LeagueRating
from dfg_rating.model.forecast.base_forecast import BaseForecast
from copy import deepcopy



class CountryLeague(BaseNetwork):
    def __init__(self, **kwargs):
        self.type='national'
        self.data=None
        self.seasons = kwargs.get('seasons', 1)
        self.country_id = kwargs.get('country_id', 0)+'_'
        self.oneleg = kwargs.get('oneleg', True)
        self.num_teams_level1 = kwargs.get('level1_teams', 12)
        self.num_teams_level2 = kwargs.get('level2_teams', 12)
        self.num_teams_level3 = kwargs.get('level3_teams', 12)
        self.promotion_number = kwargs.get('promotion_number', 2)
        self.number_of_clusters = kwargs.get('clusters', 1)
        self.n_teams = kwargs.get('teams', 0)

        kwargs['teams'] = self.n_teams
        self.n_rounds = kwargs.get('rounds', self.n_teams - 1 + self.n_teams % 2)
        kwargs['play'] = False
        self.rating_mode = kwargs.get('rating_mode', 'keep')
        
        self.min_match_level1_level2 = kwargs.get('min_match_per_team_level1_level2', 1)
        self.avg_match_level1_level2 = kwargs.get('avg_match_per_team_level1_level2', 3)

        self.min_match_level2_level3 = kwargs.get('min_match_per_team_level2_level3', 1)
        self.avg_match_level2_level3 = kwargs.get('avg_match_per_team_level2_level3', 3)

        self.min_match_level3_level1 = kwargs.get('min_match_per_team_level3_level1', 1)
        self.avg_match_level3_level1 = kwargs.get('avg_match_per_team_level3_level1', 3)

        self.min_match_level1_level1 = kwargs.get('min_match_per_team_level1_level1', 1)
        self.avg_match_level1_level1 = kwargs.get('avg_match_per_team_level1_level1', 0.2)

        self.min_match_level2_level2 = kwargs.get('min_match_per_team_level2_level2', 1)
        self.avg_match_level2_level2 = kwargs.get('avg_match_per_team_level2_level2', 0.2)

        self.min_match_level3_level3 = kwargs.get('min_match_per_team_level3_level3', 1)
        self.avg_match_level3_level3 = kwargs.get('avg_match_per_team_level3_level3', 0.2)
        
        self.team_labels = kwargs.get('team_labels', None)

        self.true_rating_level1 = kwargs.get(
            'true_rating_level1',
            ControlledTrendRating(
                starting_point=ControlledRandomFunction(distribution='normal', loc=1000, scale=50),
                delta=ControlledRandomFunction(distribution='normal', loc=0, scale=.5),
                trend=ControlledRandomFunction(distribution='normal', loc=0, scale=.2),
                season_delta=ControlledRandomFunction(distribution='normal', loc=0, scale=30),
                rating_name='true_rating'
            )
        )

        self.true_rating_level2 = kwargs.get(
            'true_rating_level2',
            ControlledTrendRating(
                starting_point=ControlledRandomFunction(distribution='normal', loc=600, scale=50),
                delta=ControlledRandomFunction(distribution='normal', loc=0, scale=.5),
                trend=ControlledRandomFunction(distribution='normal', loc=0, scale=.2),
                season_delta=ControlledRandomFunction(distribution='normal', loc=0, scale=30),
                rating_name='true_rating'
            )
        )

        self.true_rating_level3 = kwargs.get(
            'true_rating_level3',
            ControlledTrendRating(
                starting_point=ControlledRandomFunction(distribution='normal', loc=300, scale=50),
                delta=ControlledRandomFunction(distribution='normal', loc=0, scale=.5),
                trend=ControlledRandomFunction(distribution='normal', loc=0, scale=.2),
                season_delta=ControlledRandomFunction(distribution='normal', loc=0, scale=30),
                rating_name='true_rating'
            )
        )

        self.true_rating_level4 = copy.deepcopy(self.true_rating_level3)

        self.true_forecast = kwargs.get(
            'true_forecast',
            LogFunctionForecast(
                outcomes=['home', 'draw', 'away'],
                coefficients=[-0.9, 0.3],
                beta_parameter=0.006
            )
        )

        self.ranking_rating: BaseRating = kwargs.get('ranking_rating', LeagueRating())

        self.create_data()
    
    def add_odds():
        pass
    def add_bets():
        pass
    
    def select_teams(self, clusters, select_n_teams=None, season=0, selection_strategy='random'):
        def select_from_cluster(cluster, n, strategy):
            if strategy == 'random':
                return random.sample(cluster, n) if n else cluster
            elif strategy == 'top':
                if season in self.data.nodes[cluster[0]]['ratings'].get('ranking', {}):
                    return sorted(cluster, key=lambda team: (self.data.nodes[team].get('ratings', {}).get('ranking', {}).get(season, {})[-1], random.random()), reverse=True)[:n]
                else:
                    return sorted(cluster, key=lambda team: (self.data.nodes[team].get('ratings', {}).get('true_rating', {}).get(season, {})[-1], random.random()), reverse=True)[:n]
            elif strategy == 'bottom':
                if season in self.data.nodes[cluster[0]]['ratings'].get('ranking', {}):
                    return sorted(cluster, key=lambda team: (self.data.nodes[team].get('ratings', {}).get('ranking', {}).get(season, {})[-1], random.random()))[:n]
                else:
                    return sorted(cluster, key=lambda team: (self.data.nodes[team].get('ratings', {}).get('true_rating', {}).get(season, {})[-1], random.random()))[:n]
            else:
                raise ValueError(f"Unknown selection strategy: {strategy}")
        if clusters == []:
            return []
        elif isinstance(clusters[0], list):
            selected_teams = [select_from_cluster(cluster, select_n_teams, selection_strategy) for cluster in clusters]
        else:
            selected_teams = select_from_cluster(clusters, select_n_teams, selection_strategy)

        return selected_teams

    def get_promoted_teams(self, level, season):
        return getattr(self, f'promoted_teams_{level}', [])
    
    def set_edge_state(self, team1, team2, prob, season, type=''):
        def search_edge(team1, team2, season):
            return next(((u, v, key) for u, v, key, data in self.data.edges(keys=True, data=True) if data['season'] == season and u == team1 and v == team2), None)

        edges_team1_2 = search_edge(team1, team2, season)
        if edges_team1_2:
            u, v, key = edges_team1_2
            self.data.edges[u, v, key]['competition_type'] = type
            self.data.edges[v, u, key]['competition_type'] = type
            if type != 'League' or prob==0: # international and national both have inactive, national is oneleg, international is two leg
                if not self.oneleg:
                    state = 'active' if random.random() < prob else 'inactive'
                    self.data.edges[u, v, key]['state'] = state
                    self.data.edges[v, u, key]['state'] = state

                else:
                    if random.random() < 0.5: # choose direction randomly
                        self.data.edges[u, v, key]['state'] = 'active' if random.random() < prob else 'inactive'
                        self.data.edges[v, u, key]['state'] = 'inactive'

                    else:
                        self.data.edges[v, u, key]['state'] = 'active' if random.random() < prob else 'inactive'
                        self.data.edges[u, v, key]['state'] = 'inactive'
            else: # League is always two leg active
                self.data.edges[u, v, key]['state'] = 'active'
                self.data.edges[v, u, key]['state'] = 'active'

    def schedule_network(self, teams_level1, teams_level2, min_matches_per_team, avg_matches_per_team, season, oneleg=True):
        # set national cup match
        if teams_level1 != teams_level2:
            all_teams = teams_level1 + teams_level2
        else:
            all_teams = teams_level1

        num_teams = len(all_teams)
        if oneleg:
            total_matches = math.ceil((num_teams * avg_matches_per_team) / 2)
        else:
            total_matches = math.ceil((num_teams * avg_matches_per_team) / 4)

        match_pairs = set()
        team_matches = {team: 0 for team in all_teams}

        # possible_matches = [(team1, team2) for team1 in all_teams for team2 in all_teams if team1 != team2]
        if teams_level1 != teams_level2:
            possible_matches = [(team1, team2) for idx1, team1 in enumerate(teams_level1) for idx2, team2 in enumerate(teams_level2)]
        else:
            possible_matches = [(team1, team2) for idx1, team1 in enumerate(all_teams) for team2 in all_teams[idx1+1:]]

        if total_matches > len(possible_matches)*2 and oneleg:
            raise ValueError(f"Not enough possible matches to schedule {total_matches} matches with {len(possible_matches)*2} possible matches")
        if total_matches > len(possible_matches)*4 and not oneleg:
            raise ValueError(f"Not enough possible matches to schedule {total_matches} matches with {len(possible_matches)*4} possible matches")
        ### Do not consider the matches within same division:
        # for team1 in teams_level1:
        #     for team2 in teams_level1:
        #         if team1 != team2:
        #             possible_matches.append((team1, team2))

        random.shuffle(possible_matches)
        remaining_matches = possible_matches.copy()
        for match in possible_matches:
            team1, team2 = match
            # Check if both teams need more matches
            if team_matches[team1] < min_matches_per_team or team_matches[team2] < min_matches_per_team:
                if oneleg:
                    if random.choice([True, False]):
                        match = (team1, team2)
                    else:
                        match = (team2, team1)
                    match_pairs.add(match)
                    remaining_matches.remove((team1, team2))
                    team_matches[team1] += 1
                    team_matches[team2] += 1
                else:
                    # Schedule both home and away matches
                    match_pairs.add((team1, team2))
                    match_pairs.add((team2, team1))
                    remaining_matches.remove(match)
                    team_matches[team1] += 2
                    team_matches[team2] += 2
            else:
                # Both teams have met the minimum matches requirement
                continue
            # Check if all teams have met the minimum matches requirement
            if all([team_matches[team] >= min_matches_per_team for team in all_teams]):
                break
        
        while remaining_matches!=[] and len(match_pairs)<total_matches:
            pair = remaining_matches.pop()
            team1, team2 = pair
            if oneleg:
                if random.choice([True, False]):
                    match = (team1, team2)
                else:
                    match = (team2, team1)
                match_pairs.add(match)
                team_matches[team1] += 1
                team_matches[team2] += 1
            else:
                # Schedule both home and away matches
                match_pairs.add((team1, team2))
                match_pairs.add((team2, team1))
                team_matches[team1] += 2
                team_matches[team2] += 2

        
        # random choose day during 365 days
        match_schedule = []
        available_days = list(range(1, 366))
        for match in match_pairs:
            day = random.choice(available_days)
            match_schedule.append((match[0], match[1], day))
        
        match_schedule.sort(key=lambda x: x[2])  # sort by match day
        for match in match_schedule:
            self.data.add_edge(
                match[0],
                match[1],
                season=season, round=match[2], day=match[2], competition_type='National'
            )
            # print(f"{match[0]} vs {match[1]} on Day {match[2]}")
    
    def fill_graph(self, season=0):

        if self.team_labels is not None:
            teams_list = list(self.team_labels.keys())
        else:
            teams_list = list(range(0, self.n_teams))
            self.team_labels = {i: i for i in range(self.n_teams)}
        
        # Add country_id prefix node id
        teams_list = [self.country_id + str(team) for team in teams_list]
        self.team_labels = {self.country_id + str(k): v for k, v in self.team_labels.items()}

        if self.data is None:
            graph = nx.MultiDiGraph()
            graph.add_nodes_from([t for t in teams_list])
            self.data = graph
        
        # get 3 level's team idx
        if season == 0:
            self.teams_level1, self.teams_level2, self.teams_level3, self.teams_level4 = teams_list[:self.num_teams_level1], teams_list[self.num_teams_level1:self.num_teams_level1+self.num_teams_level2], teams_list[self.num_teams_level1+self.num_teams_level2:self.num_teams_level1+self.num_teams_level2+self.num_teams_level3], teams_list[self.num_teams_level1+self.num_teams_level2+self.num_teams_level3:]
            self.teams_rating_level1 = self.teams_level1.copy()
            self.teams_rating_level2 = self.teams_level2.copy()
            self.teams_rating_level3 = self.teams_level3.copy()
            self.teams_rating_level4 = self.teams_level4.copy()
            self.teams_level = {}
            for team in self.team_labels:
                self.teams_level[team] = {}
                self.teams_level[team][season] = 'level1' if team in self.teams_level1 else 'level2' if team in self.teams_level2 else 'level3' if team in self.teams_level3 else 'level4'

        print('level1:',self.teams_level1)
        print('level2:',self.teams_level2)
        print('level3:',self.teams_level3)

        for level in ['level1', 'level2', 'level3', 'level4']:
            # set league match first
            number_of_teams = len(getattr(self, f'teams_{level}'))
            number_of_rounds = number_of_teams - 1 + number_of_teams % 2
            n_games_per_round = int(math.ceil(number_of_teams / 2))
            if number_of_teams % 2 != 0:
                getattr(self, f'teams_{level}').append(-1)
            slice_a = getattr(self, f'teams_{level}')[0:n_games_per_round]
            slice_b = getattr(self, f'teams_{level}')[n_games_per_round:]
            fixed = getattr(self, f'teams_{level}')[0]
            days_between_rounds = 364 / (number_of_rounds*2 - 1)
            day = 1
            for season_round in range(0, number_of_rounds):
                for game in range(0, n_games_per_round):
                    if (slice_a[game] != -1) and (slice_b[game] != -1):
                        if season_round % 2 == 0:
                            self.data.add_edge(
                                slice_a[game],
                                slice_b[game],
                                season=season, round=season_round, day=int(day), competition_type='League'
                            )
                            self.data.add_edge(
                                slice_b[game],
                                slice_a[game],
                                season=season, round=season_round + number_of_rounds,
                                day=int(day + (number_of_rounds * days_between_rounds)),
                                competition_type='League'
                            )
                        else:
                            self.data.add_edge(
                                slice_b[game],
                                slice_a[game],
                                season=season, round=season_round, day=int(day), competition_type='League'
                            )
                            self.data.add_edge(
                                slice_a[game],
                                slice_b[game],
                                season=season, round=season_round + number_of_rounds,
                                day=int(day + (number_of_rounds * days_between_rounds)),
                                competition_type='League'
                            )
                day += days_between_rounds
                rotate = slice_a[-1]
                slice_a = [fixed, slice_b[0]] + slice_a[1:-1]
                slice_b = slice_b[1:] + [rotate]
            try:
                getattr(self, f'teams_{level}').remove(-1)
            except ValueError:
                pass  

    def add_rating(self, rating_name='true_rating', mode='keep', season=0):
        """
        for each level, add rating to each team
        
        mode: 'keep', 'mix', 'interchange'
        - keep mode will keep the rating of the team when team get promoted or relegated
        - mix mode will Same ratings + season delta + division mean difference
        - Interchange of ratings between promoted and relegated teams but keeping the original difference between teams. For example:
        A, B, and C will relegate with ratings 8, 4, and 2, respectively. X, Y, Z will promote with ratings 1, 2, 3. A, B, C they will get values that have an average with 3, but keep that C = 2B = 4A

        """
        for level in ['level1', 'level2', 'level3', 'level4']:
            rating_values, rating_hp = getattr(self, f'true_rating_{level}').get_ratings(
                self, level, season
            )
            if mode == 'keep':
                for team in getattr(self, f'teams_rating_{level}'):
                    index_of_team = getattr(self,f'teams_rating_{level}').index(team)
                    self._add_rating_to_team(team, rating_values[index_of_team], rating_hp, rating_name, season=season)
                    print('team:',team, 'rating_start:',rating_values[index_of_team][0], 'rating_end:',rating_values[index_of_team][-1])
            elif mode == 'mix' or mode == 'interchange':
                for team in getattr(self, f'teams_{level}'):
                    index_of_team = getattr(self,f'teams_{level}').index(team)
                    self._add_rating_to_team(team, rating_values[index_of_team], rating_hp, rating_name, season=season)
                    print('team:',team, 'rating_start:',rating_values[index_of_team][0], 'rating_end:',rating_values[index_of_team][-1])
    
    def remove_division4_teams(self, season):
        matches_of_4division = [(u,v,key,data) for u,v,key,data in self.data.edges(keys=True, data=True) if data['competition_type']=='League' and data['season']==season and (u in self.teams_level4 or v in self.teams_level4)]
        self.data.remove_edges_from(matches_of_4division)
    
    def get_avaliable_rating(self, team, match_day, season):
        league_matches = [
                        (u, v, data['day'], data['round']) 
                        for u, v, key, data in self.data.edges(keys=True, data=True) 
                        if data['season'] == season and data['competition_type'] == 'League' and (u == team or v == team)
                    ]
        closest_round = max([(day, round) for _, _, day, round in league_matches if day <= match_day], default=None, key=lambda x:x[0])[1]
        rating = self.data.nodes[team].get('ratings', {}).get('true_rating', {}).get(season, 0)[closest_round+1]
        return rating, closest_round
    
    def add_forecast(self, forecast, forecast_name, season=0):
        for match in self.data.edges(keys=True):
            if self.data.edges[match].get('season', 0) == season:
                if self.data.edges[match].get('competition_type', '') == 'League':
                    super()._add_forecast_to_team(match, deepcopy(forecast), forecast_name, 'true_rating')
                elif self.data.edges[match].get('competition_type', '') == 'National':
                    match_day = self.data.edges[match].get('day', 1)
                    home_rating, home_closest_round = self.get_avaliable_rating(match[1],match_day,season)
                    away_rating, away_clostest_round = self.get_avaliable_rating(match[0],match_day,season)
                    forecast_object = deepcopy(forecast)
                    diff = forecast_object.home_error.apply(home_rating) - forecast_object.away_error.apply(away_rating)
                    for i in range(len(forecast_object.outcomes)):
                        n = len(forecast_object.outcomes)
                        j = i+1
                        forecast_object.probabilities[i]=forecast_object.logit_link_function(n-j+1,diff)-forecast_object.logit_link_function(n-j,diff)
                    forecast_object.computed = True
                    self.data.edges[match].setdefault('forecasts', {})['true_forecast'] = forecast_object

    def play_sub_network(self, season):
        season_games = list(filter(lambda match: match[3].get('season', -1) == season, self.iterate_over_games())) # already sorted
        for away_team, home_team, edge_key, edge_attributes in season_games:
            f = abs(edge_attributes['forecasts']['true_forecast'].probabilities)
            weights = f.cumsum()
            x = np.random.default_rng().uniform(0, 1)
            for i in range(len(weights)):
                if x < weights[i]:
                    winner = self.true_forecast.outcomes[i]
                    self.data.edges[away_team, home_team, edge_key]['winner'] = winner
                    break

    def promote_relegate_teams(self, season):
        levels = ['level1', 'level2', 'level3', 'level4']
        promoted_teams = []
        relegated_teams = []
        # get promoted and relegated teams based on ranking
        for level in levels:
            # if self.promotion_number <= len(getattr(self, f'teams_{level}'))/2:
            #     promote = self.select_teams(getattr(self, f'teams_{level}'), self.promotion_number, season=season, selection_strategy='top')
            #     relegate = self.select_teams(getattr(self, f'teams_{level}'), self.promotion_number, season=season, selection_strategy='bottom')
            # else:
            promote = self.select_teams(getattr(self, f'teams_{level}'), self.promotion_number, season=season, selection_strategy='top')
            remaining_teams = [team for team in getattr(self, f'teams_{level}') if team not in promote]
            relegate = self.select_teams(remaining_teams, self.promotion_number, season=season, selection_strategy='bottom')
            promoted_teams.extend(promote)
            relegated_teams.extend(relegate)
            setattr(self, f'promoted_teams_{level}', promote)
            setattr(self, f'relegated_teams_{level}', relegate)

        for team in promoted_teams:
            current_level = self.teams_level[team][season]
            next_level = f'level{int(current_level[-1]) - 1}' if current_level != 'level1' else 'level1'
            self.teams_level[team][season + 1] = next_level

        for team in relegated_teams:
            current_level = self.teams_level[team][season]
            if self.teams_level4 != []:
                next_level = f'level{int(current_level[-1]) + 1}' if current_level != 'level4' else 'level4'
            else:
                next_level = f'level{int(current_level[-1]) + 1}' if current_level != 'level3' else 'level3'
            self.teams_level[team][season + 1] = next_level
        for team, seasons in self.teams_level.items():
            if season + 1 not in seasons:
                seasons[season + 1] = seasons[season]
        for level in levels:
            setattr(self, f'teams_{level}', [team for team in self.teams_level.keys() if self.teams_level[team][season + 1] == level])

    def create_data(self):
        for season in range(self.seasons):
            print('--------------- season:', season, '----------------')
            # season = 0
            
            # fill the league graph and add rating
            self.fill_graph(season=season)
            self.add_rating(rating_name='true_rating', mode=self.rating_mode, season=season)
            self.remove_division4_teams(season)
            # schedule the national matches
            levels = [
                (self.teams_level1, self.teams_level2, self.min_match_level1_level2, self.avg_match_level1_level2),
                (self.teams_level1, self.teams_level3, self.min_match_level3_level1, self.avg_match_level3_level1),
                (self.teams_level2, self.teams_level3, self.min_match_level2_level3, self.avg_match_level2_level3),
                (self.teams_level1, self.teams_level1, self.min_match_level1_level1, self.avg_match_level1_level1),
                (self.teams_level2, self.teams_level2, self.min_match_level2_level2, self.avg_match_level2_level2),
                (self.teams_level3, self.teams_level3, self.min_match_level3_level3, self.avg_match_level3_level3)
            ]
            for level1, level2, min_match, avg_match in levels:
                self.schedule_network(level1, level2, min_match, avg_match, season, self.oneleg)
            

            # add forecast to all games
            self.add_forecast(self.true_forecast, 'true_forecast', season=season)
            
            # play this season
            
            self.play_sub_network(season)
            print('********** playing season:', season, '*********')
            
            # based on the reslut of game, give ranking
            levels = ['level1', 'level2', 'level3']
            for level in levels:
                print('*******', level)
                ratings, rating_hp = self.ranking_rating.get_ratings(self, getattr(self, f'teams_{level}'), season=season, level=level)
                for team in getattr(self, f'teams_{level}'):
                    index_of_team = getattr(self,f'teams_{level}').index(team)
                    self._add_rating_to_team(team, ratings[index_of_team], rating_hp, 'ranking', season=season)
                    print('team:',team, 'ranking_end_season:',ratings[index_of_team][-1])
            
            self.promote_relegate_teams(season)

        return True

    def get_mean_rating(self, rating_name, season, level, default_rating):
        ratings_list = []
        team_ids = [team_id for team_id, seasons in self.teams_level.items() if season in seasons.keys() and seasons[season]== level]
        for t in team_ids:
            last_season_rating = self.data.nodes[t].get('ratings', {}).get(rating_name, {}).get(season, 0)[-1]
            ratings_list.append(last_season_rating)
        return default_rating[0] if len(ratings_list) == 0 else np.mean(ratings_list)

    def export(self, file_name='network.csv', printing_ratings=['true_rating'], printing_forecasts=['true_forecast']):
        print("Export network")
        network_flat = []
        for away_team, home_team, edge_key, edge_attributes in self.iterate_over_games():
            match_dict = {
                "Home": home_team,
                "Home_level": self.teams_level[home_team].get(edge_attributes.get('season', 0), 'level1'),
                "Home_country": home_team.split('_')[0],
                "Away": away_team,
                "Away_level": self.teams_level[away_team].get(edge_attributes.get('season', 0), 'level1'),
                "Away_country": away_team.split('_')[0],
                "Season": edge_attributes.get('season', 0),
                "Round": edge_attributes.get('round', -1),
                "Day": edge_attributes.get('day', -1),
                "Result": edge_attributes.get('winner', 'none'),
                'competition_type': edge_attributes.get('competition_type', 'League')
            }
            for f in printing_forecasts:
                forecast_object: BaseForecast = edge_attributes.get('forecasts', {}).get(f, None)
                if forecast_object is not None:
                    for i, outcome in enumerate(forecast_object.outcomes):
                        match_dict[f"{f}#{outcome}"] = forecast_object.probabilities[i]
            for r in printing_ratings:
                for team, name in [(home_team, 'Home'), (away_team, 'Away')]:
                    if edge_attributes.get('competition_type', '') == 'League' and r!='elo_rating':
                        rating_dict = self.data.nodes[team].get('ratings', {}).get(r, {})
                        match_dict[f"{r}#{name}"] = rating_dict.get(edge_attributes.get('season', 0), 0)[edge_attributes.get('round', 0)]
                    elif r=='elo_rating':
                        rating_dict = self.data.nodes[team].get('ratings', {}).get(r, {})
                        match_dict[f"{r}#{name}"] = rating_dict.get(edge_attributes.get('season', 0), 0)[edge_attributes.get('day', 1)-1]
                    elif r!='ranking': # for national match, there is no ranking avaliable
                        match_dict[f"{r}#{name}"] = self.get_avaliable_rating(team, edge_attributes.get('day', 1), edge_attributes.get('season', 0))[0]
            network_flat.append(match_dict)
        df = pd.DataFrame(network_flat)
        df.to_csv(file_name, index=False)


class InternationalCompetition_Combine(BaseNetwork):
    def __init__(self, **kwargs):
        """
        InternationalCompetition class
        """
        self.type='international'
        self.countries_configs = kwargs.get('countries_configs', {})
        self.avg_match_per_team = kwargs.get('avg_match_per_team', 3)
        self.min_match_per_team = kwargs.get('min_match_per_team', 1)
        # self.international_prob = kwargs.get('match_prob', 0.1)
        self.oneleg = kwargs.get('oneleg', False)
        self.teams_per_country = kwargs.get('teams_per_country', 3)
        self.countries_leagues = {}
        self.seasons = kwargs.get('seasons', 1)
        # self.days_between_rounds = kwargs.get('days_between_rounds', 1)
        self.choose_mode = kwargs.get('choose_mode', 'random')
        self.team_id_map = {}  # map from original team id to new unique team id
        self.selected_teams_list = []
        self.team_level_map = {}
        self.number_of_clusters = kwargs.get('clusters', 1) # for visualization
        self.true_forecast = kwargs.get(
            'true_forecast',
            LogFunctionForecast(
                outcomes=['home', 'draw', 'away'],
                coefficients=[-0.9, 0.3],
                beta_parameter=0.006
            )
        )
        
        if kwargs.get('create_country_network', True):
            # generate all countries data
            self.total_teams = 0
            for country_idx, country_config in self.countries_configs.items():
                print('country:', country_idx)
                country_config['seasons'] = self.seasons
                country_league = CountryLeague(**country_config)
                # self.data = nx.compose(self.data, country_league.data)
                self.countries_leagues[country_idx] = country_league
                # self.team_level_map[country_idx] = {'level1': country_league.teams_level1, 'level2': country_league.teams_level2, 'level3': country_league.teams_level3}
                
                self.total_teams+=country_config.get('teams', 0)
            self.n_teams = self.total_teams
            self.n_rounds = kwargs.get('rounds', self.n_teams - 1 + self.n_teams % 2)
        else:
            self.total_teams=0
            for country_idx, country_config in self.countries_configs.items():
                self.total_teams+=country_config.n_teams
                self.countries_leagues[country_idx] = country_config
        self.create_data()
    
    def add_bets(self):
        pass

    def add_forecast(self, season):
        for match in self.data.edges(keys=True):
            if self.data.edges[match].get('season', 0) == season and self.data.edges[match].get('competition_type', '') == 'international':
                match_day = self.data.edges[match].get('day', 1)
                home_id = match[1]
                away_id = match[0]
                home_country_id = home_id.split('_')[0]
                away_country_id = away_id.split('_')[0]
                
                home_rating, home_closest_round = self.countries_leagues[home_country_id].get_avaliable_rating(home_id, match_day, season)
                away_rating, away_closest_round = self.countries_leagues[away_country_id].get_avaliable_rating(away_id, match_day, season)
                forecast_object = deepcopy(self.true_forecast)
                diff = forecast_object.home_error.apply(home_rating) - forecast_object.away_error.apply(away_rating)
                for i in range(len(forecast_object.outcomes)):
                    n = len(forecast_object.outcomes)
                    j = i+1
                    forecast_object.probabilities[i]=forecast_object.logit_link_function(n-j+1,diff)-forecast_object.logit_link_function(n-j,diff)
                forecast_object.computed = True
                self.data.edges[match].setdefault('forecasts', {})['true_forecast'] = forecast_object

    def add_odds(self):
        pass
    
    def iterate_over_games(self):
        all_matches = []
        for country_id, country_league in self.countries_leagues.items():
            all_matches.extend(country_league.iterate_over_games()) # get all national and league matches
        all_matches.extend(self.data.edges(keys=True, data=True)) # add international matches
        return sorted(all_matches, key=lambda x: (x[3]['season'], x[3]['day'], x[3]['round'], x[0], x[1]))

    def _add_rating_to_team(self, team_id, rating_values, rating_hyperparameters, rating_name, season=-1):
        if season is None:
            season = 0
        country_id = team_id.split('_')[0]
        self.countries_leagues[country_id]._add_rating_to_team(team_id, rating_values, rating_hyperparameters, rating_name, season)

    def add_rating(self, rating, rating_name):
        for s in range(self.seasons):
            ratings, player_dict = rating.get_all_ratings(self, season=s)
            for t, t_i in player_dict.items():
                self._add_rating_to_team(t, ratings[t_i], {}, rating_name, season=s)
        
        self.iterate_over_games()

    def cleanup_national_networks(self):
        import gc
        del self.countries_leagues
        gc.collect() # trigger garbage collection

    def play_sub_network(self, season):
        international_games = [(u,v,k,data) for u,v,k,data in self.data.edges(keys=True, data=True) if data['season'] == season and data.get('competition_type','')=='international']
        international_games_sorted = sorted(international_games, key=lambda x: x[3]['day'])
        for away_team, home_team, edge_key, edge_attributes in international_games_sorted:
            f = abs(edge_attributes['forecasts']['true_forecast'].probabilities)
            weights = f.cumsum()
            x = np.random.default_rng().uniform(0, 1)
            for i in range(len(weights)):
                if x < weights[i]:
                    winner = self.true_forecast.outcomes[i]
                    self.data.edges[away_team, home_team, edge_key]['winner'] = winner
                    break

    def fill_graph(self, season=0, oneleg=False):
        teams_list = self.international_teams_list[season-1]
        number_of_teams = len(teams_list)

        if oneleg:
            total_matches = math.ceil((number_of_teams * self.avg_match_per_team) / 2)
        else:
            total_matches = math.ceil((number_of_teams * self.avg_match_per_team) / 4)

        match_pairs = set()
        team_matches = {team: 0 for team in teams_list}

        possible_matches = [(team1, team2) for idx1, team1 in enumerate(teams_list) for team2 in teams_list[idx1+1:]]
        random.shuffle(possible_matches)
        # print(possible_matches)
        remaining_matches = possible_matches.copy()
        for match in possible_matches:
            team1, team2 = match
            # Check if both teams need more matches
            if team_matches[team1] < self.min_match_per_team or team_matches[team2] < self.min_match_per_team:
                if oneleg:
                    if random.choice([True, False]):
                        match = (team1, team2)
                    else:
                        match = (team2, team1)
                    match_pairs.add(match)
                    remaining_matches.remove((team1, team2))
                    team_matches[team1] += 1
                    team_matches[team2] += 1
                else:
                    # Schedule both home and away matches
                    match_pairs.add((team1, team2))
                    match_pairs.add((team2, team1))
                    remaining_matches.remove(match)
                    team_matches[team1] += 2
                    team_matches[team2] += 2
            else:
                # Both teams have met the minimum matches requirement
                continue
            # Check if all teams have met the minimum matches requirement
            if all([team_matches[team] >= self.min_match_per_team for team in teams_list]):
                break
        
        while remaining_matches!=[] and len(match_pairs)<total_matches*2:
            pair = remaining_matches.pop()
            team1, team2 = pair
            if oneleg:
                if random.choice([True, False]):
                    match = (team1, team2)
                else:
                    match = (team2, team1)
                match_pairs.add(match)
                team_matches[team1] += 1
                team_matches[team2] += 1
            else:
                # Schedule both home and away matches
                match_pairs.add((team1, team2))
                match_pairs.add((team2, team1))
                team_matches[team1] += 2
                team_matches[team2] += 2
            
        match_schedule = []
        available_days = list(range(1, 366))
        for match in match_pairs:
            day = random.choice(available_days)
            match_schedule.append((match[0], match[1], day))
        
        match_schedule.sort(key=lambda x: x[2])
        for match in match_schedule:
            self.data.add_edge(
                match[0],
                match[1],
                season=season, round=match[2], day=match[2], competition_type='international'
            )
            # print(f"{match[0]} vs {match[1]} on Day {match[2]}")

    def set_edge_state(self, season):
        teams_list = self.international_teams_list[season-1]
        for t1 in teams_list:
            for t2 in teams_list:
                if t1 != t2:
                    edges_team1_2 = [(u, v, key) for u, v, key, data in self.data.edges(keys=True, data=True) if data['season'] == season and ((u == t1 and v == t2) or (u==t2 and v==t1)) and data.get('competition_type','')=='international']
                    if edges_team1_2 and not self.oneleg:
                        if random.random() < self.international_prob:
                            for match in edges_team1_2:
                                u, v, key = match
                                self.data.edges[u, v, key]['state'] = 'active'
                                self.data.edges[v, u, key]['state'] = 'active'
                        else:
                            for match in edges_team1_2:
                                u, v, key = match
                                self.data.edges[u, v, key]['state'] = 'inactive'
                                self.data.edges[v, u, key]['state'] = 'inactive'
    
    def select_teams(self):
        if self.data is None:
            self.data = nx.MultiDiGraph()
        
        self.international_teams_list = {}
        for season in range(self.seasons):
            print('international competitinon after season: ', season)
            
            # choose each country's teams
            self.international_teams_list[season] = []
            for country_idx, country_league in self.countries_leagues.items():
                clusters = [team for team,seasons in country_league.teams_level.items() if seasons[season] == 'level1']
                selected_teams = country_league.select_teams(clusters, self.teams_per_country, season, self.choose_mode)
                for t in selected_teams:
                    self.international_teams_list[season].append(t)
                    self.data.add_node(t, **self.countries_leagues[country_idx].data.nodes[t]) #directly use original node-attribute object
            print(f'internaiontal season {season}: {self.international_teams_list[season]}')
        # self.cleanup_national_networks()
    
    def merge_graph(self):
        merged_graph = nx.MultiDiGraph()
        
        current_node_idx = self.total_teams-1
        country_node_mapping = {}

        for country_idx, country_league in self.countries_leagues.items():
            country_node_mapping[country_idx] = {}
            for node in country_league.data.nodes:
                new_node = current_node_idx
                country_node_mapping[country_idx][node] = new_node
                current_node_idx-=1
            relabeled_graph = nx.relabel_nodes(country_league.data, country_node_mapping[country_idx])
            merged_graph = nx.compose(merged_graph, relabeled_graph)
        self.data = merged_graph

        for country_idx, country_league in country_node_mapping.items():
            print('country:', country_idx)
            for node in country_league:
                print('node:', node, 'mapped:', country_league[node])
        return country_node_mapping

    def check_data(self, country_node_mapping):
        print('check data')
        competition_type_colors={
            'League': 'blue',
            'National': 'green',
            'international': 'red'
        }
        node_type_colors = {
            'level1': 'blue',
            'level2': 'green',
            'level3': 'red',
            'level4': 'yellow'
        }
        def find_team_id_in_country(country_node_mapping, team_id):
            for country_id, teams in country_node_mapping.items():
                for original_id, mapped_id in teams.items():
                    if mapped_id == team_id:
                        return country_id, original_id
            return None, None
        import matplotlib.pyplot as plt
        for season in range(self.seasons):
            plt.figure(figsize=(10,10))
            pos=nx.spring_layout(self.data, k=1.0)
            edges = [(u, v, k) for u, v, k, d in self.data.edges(keys=True, data=True) if d['season'] == season and d['state']=='active']
            edge_colors = [competition_type_colors[self.data.edges[u,v,k]['competition_type']] for u, v, k in edges]

            node_colors = []
            labels = {}
            for n in self.data.nodes:
                country, original_id = find_team_id_in_country(country_node_mapping, n)
                level = self.countries_leagues[country].teams_level[original_id][season]
                node_colors.append(node_type_colors[level])
                labels[n] = f'{n}:{original_id}'
            nx.draw_networkx_nodes(self.data, pos,node_color=node_colors, node_size=500)
            nx.draw_networkx_edges(self.data, pos, edgelist=edges, edge_color=edge_colors)
            nx.draw_networkx_labels(self.data, pos, labels,font_color='black')
            plt.title(f'Season {season}')
            plt.show()
            plt.savefig(f'season_{season}.png')

    def get_all_teams(self):
        return [team for nation in self.countries_leagues.values() for team in nation.data.nodes]

    def create_data(self):
        self.data = nx.MultiDiGraph()
        # self.check_data(country_node_mapping)
        self.select_teams()
        
        for season in range(1, self.seasons):
            # ###### skip first season

            self.fill_graph(season, self.oneleg)
            # self.set_edge_state(season)
            
            print(f'play International Competition Season {season-1}')
            self.add_forecast(season)
            self.play_sub_network(season)
    
    def get_playing_teams(self, season):
        pass
        # playing_teams = []
        # for national_network in self.countries_leagues.values():
        #     playing_teams.extend(national_network.teams_level1)
        #     playing_teams.extend(national_network.teams_level2)
        #     playing_teams.extend(national_network.teams_level3)
        # return playing_teams

    def export(self, file_name='network.csv', printing_ratings=['true_rating'], printing_forecasts=['true_forecast']):
        print("Export network")
        network_flat = []
        for away_team, home_team, edge_key, edge_attributes in self.iterate_over_games():
            match_dict = {
                "Home": home_team,
                "Home_level": self.countries_leagues[home_team.split('_')[0]].teams_level[home_team].get(edge_attributes.get('season', 0), 'level1'),
                "Home_country": home_team.split('_')[0],
                "Away": away_team,
                "Away_level": self.countries_leagues[away_team.split('_')[0]].teams_level[away_team].get(edge_attributes.get('season', 0), 'level1'),
                "Away_country": away_team.split('_')[0],
                "Season": edge_attributes.get('season', 0),
                "Round": edge_attributes.get('round', -1),
                "Day": edge_attributes.get('day', -1),
                "Result": edge_attributes.get('winner', 'none'),
                'competition_type': edge_attributes.get('competition_type', 'League')
            }
            for f in printing_forecasts:
                forecast_object: BaseForecast = edge_attributes.get('forecasts', {}).get(f, None)
                if forecast_object is not None:
                    for i, outcome in enumerate(forecast_object.outcomes):
                        match_dict[f"{f}#{outcome}"] = forecast_object.probabilities[i]
            for r in printing_ratings:
                for team, name in [(home_team, 'Home'), (away_team, 'Away')]:
                    country_id = team.split('_')[0]
                    country_network = self.countries_leagues[country_id]
                    if edge_attributes.get('competition_type', '') == 'League' and r!='elo_rating':
                        rating_dict = country_network.data.nodes[team].get('ratings', {}).get(r, {})
                        match_dict[f"{r}#{name}"] = rating_dict.get(edge_attributes.get('season', 0), 0)[edge_attributes.get('round', 0)]
                    elif r=='elo_rating':
                        rating_dict = country_network.data.nodes[team].get('ratings', {}).get(r, {})
                        match_dict[f"{r}#{name}"] = rating_dict.get(edge_attributes.get('season', 0), 0)[edge_attributes.get('day', 1)-1]
                    elif r!='ranking': # for inter/national match, there is no ranking avaliable
                        match_dict[f"{r}#{name}"] = country_network.get_avaliable_rating(team, edge_attributes.get('day', 1), edge_attributes.get('season', 0))[0]
            network_flat.append(match_dict)
        df = pd.DataFrame(network_flat)
        df.to_csv(file_name, index=False)