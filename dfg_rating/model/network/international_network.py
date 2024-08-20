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
from dfg_rating.model.rating.controlled_trend_rating import ControlledTrendRating, ControlledRandomFunction
from dfg_rating.model.rating.base_rating import BaseRating
from dfg_rating.model.rating.ranking_rating import LeagueRating
from dfg_rating.model.forecast.base_forecast import BaseForecast
from copy import deepcopy



class CountryLeague(RoundRobinNetwork):
    def __init__(self, **kwargs):
        self.oneleg = kwargs.get('oneleg', True)
        self.num_teams_level1 = kwargs.get('level1_teams', 12)
        self.num_teams_level2 = kwargs.get('level2_teams', 12)
        self.num_teams_level3 = kwargs.get('level3_teams', 12)
        self.promotion_number = kwargs.get('promotion_number', 2)
        self.n_teams = kwargs.get('teams', 0)
        # self.n_playing = self.num_teams_level1 + self.num_teams_level2 + self.num_teams_level3
        kwargs['teams'] = self.n_teams
        kwargs['play'] = False
        self.rating_mode = kwargs.get('rating_mode', 'keep')
        

        self.prob_level1_level2 = kwargs.get('prob_level1_level2', 0.4)
        self.prob_level1_level3 = kwargs.get('prob_level1_level3', 0.3)
        self.prob_level2_level3 = kwargs.get('prob_level2_level3', 0.2)
        
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

        super().__init__(**kwargs)
    
    # def select_teams(self, cluster_1, cluster_2, prob, season, select_n_teams=None, set_edge_state=False):
    def select_teams(self, clusters, select_n_teams=None, season=0, selection_strategy='random'):
        def select_from_cluster(cluster, n, strategy):
            if strategy == 'random':
                return random.sample(cluster, n) if n else cluster
            elif strategy == 'top':
                return sorted(cluster, key=lambda team: self.data.nodes[team].get('ratings', {}).get('ranking', {}).get(season, {})[-1], reverse=True)[:n]
            elif strategy == 'bottom':
                return sorted(cluster, key=lambda team: self.data.nodes[team].get('ratings', {}).get('ranking', {}).get(season, {})[-1])[:n]
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

    
    def fill_graph(self, season=0):

        if self.team_labels is not None:
            teams_list = list(self.team_labels.keys())
        else:
            teams_list = list(range(0, self.n_teams))
            self.team_labels = {i: i for i in range(self.n_teams)}
        if self.data is None:
            graph = nx.MultiDiGraph()
            graph.add_nodes_from([t for t in teams_list])
            self.data = graph
        super().fill_graph(self.team_labels, season)

        
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


        clusters_probabilities = [
            (self.teams_level1, self.teams_level1, 1, 'League'),
            (self.teams_level2, self.teams_level2, 1, 'League'),
            (self.teams_level3, self.teams_level3, 1, 'League'),
            (self.teams_level1, self.teams_level2, self.prob_level1_level2, 'National'),
            (self.teams_level1, self.teams_level3, self.prob_level1_level3, 'National'),
            (self.teams_level2, self.teams_level3, self.prob_level2_level3, 'National'),
            (self.teams_level1, self.teams_level4, 0, 'National'),
            (self.teams_level2, self.teams_level4, 0, 'National'),
            (self.teams_level3, self.teams_level4, 0, 'National'),
            (self.teams_level4, self.teams_level4, 0, 'League')
        ]

        for cluster1, cluster2, prob, type in clusters_probabilities:
            # selected_teams = self.select_teams([cluster1, cluster2], season)
            selected_teams = [cluster1, cluster2] # dont need select
            for team1 in selected_teams[0]:
                for team2 in selected_teams[1]:
                    self.set_edge_state(team1, team2, prob, season, type)
    

    def add_rating(self, rating_name='true_rating', mode='keep', season=0):
        def edge_filter(e):
            return e[3]['season'] == season
        """
        for each level, add rating to each team
        
        mode: 'keep', 'mix', 'interchange'
        - keep mode will keep the rating of the team when team get promoted or relegated
        - mix mode will Same ratings + season delta + division mean difference
        - Interchange of ratings between promoted and relegated teams but keeping the original difference between teams. For example:
        A, B, and C will relegate with ratings 8, 4, and 2, respectively. X, Y, Z will promote with ratings 1, 2, 3. A, B, C they will get values that have an average of 2, but keep that C = 2B = 4A

        """
        for level in ['level1', 'level2', 'level3', 'level4']:
            if rating_name=='true_rating':
                rating_values, rating_hp = getattr(self, f'true_rating_{level}').get_cluster_ratings(
                    self, level, edge_filter, season
                )
                if mode == 'keep':
                    for team in getattr(self, f'teams_rating_{level}'):
                        index_of_team = getattr(self,f'teams_rating_{level}').index(team)
                        self._add_rating_to_team(team, rating_values[index_of_team], rating_hp, rating_name, season=season)
                        print('team:',team, 'rating_start:',rating_values[index_of_team][0])
                elif mode == 'mix' or mode == 'interchange':
                    for team in getattr(self, f'teams_{level}'):
                        index_of_team = getattr(self,f'teams_{level}').index(team)
                        self._add_rating_to_team(team, rating_values[index_of_team], rating_hp, rating_name, season=season)
                        print('team:',team, 'rating_start:',rating_values[index_of_team][0])


    def create_data(self):
        for season in range(self.seasons):
            print('--------------- season:', season, '----------------')
            # season = 0
            
            # fill the country graph
            self.fill_graph(season=season)
            
            self.add_rating(rating_name='true_rating', mode=self.rating_mode, season=season)
            levels = ['level1', 'level2', 'level3', 'level4']
            # # add each level's rating
            # for level in levels:
            #     def edge_filter(e):
            #         return e[3]['season'] == season
            #     rating_values, rating_hp = getattr(self, f'true_rating_{level}').get_cluster_ratings(
            #     self, getattr(self, f'teams_rating_{level}'), edge_filter, season
            #     )
            #     for team in getattr(self, f'teams_rating_{level}'):
            #         index_of_team = getattr(self,f'teams_rating_{level}').index(team)
            #         self._add_rating_to_team(team, rating_values[index_of_team], rating_hp, 'true_rating', season=season) # only one by one
            #         print('team:',team, 'rating_start:',rating_values[index_of_team][0])
            
            
            # add forecast to all games
            super().add_forecast(self.true_forecast, 'true_forecast', season=season)
            
            # play this season
            season_games = list(filter(lambda match: match[3].get('season', -1) == season, self.iterate_over_games()))
            self.play_sub_network(season_games)
            print('********** playing season:', season, '*********')
            
            # based on the reslut of game, give ranking
            for level in levels:
                print('*******', level)
                ratings, rating_hp = self.ranking_rating.get_cluster_ratings(self, getattr(self, f'teams_{level}'), season=season, level=level)
                for team in getattr(self, f'teams_{level}'):
                    index_of_team = getattr(self,f'teams_{level}').index(team)
                    self._add_rating_to_team(team, ratings[index_of_team], rating_hp, 'ranking', season=season)
                    print('team:',team, 'ranking_end_season:',ratings[index_of_team][-1])
            promoted_teams = []
            relegated_teams = []
            # get promoted and relegated teams based on ranking
            for level in levels:
                if self.promotion_number <= len(getattr(self, f'teams_{level}'))/2:
                    promote = self.select_teams(getattr(self, f'teams_{level}'), self.promotion_number, season=season, selection_strategy='top')
                    relegate = self.select_teams(getattr(self, f'teams_{level}'), self.promotion_number, season=season, selection_strategy='bottom')
                else:
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

            # for team in self.promoted_teams_level2:
            #     self.teams_level1.append(team)
            #     self.teams_level2.remove(team)
            # for team in self.relegated_teams_level1:
            #     self.teams_level1.remove(team)
            #     self.teams_level2.append(team)
            # for team in self.promoted_teams_level3:
            #     self.teams_level2.append(team)
            #     self.teams_level3.remove(team)
            # for team in self.relegated_teams_level2:
            #     self.teams_level2.remove(team)
            #     self.teams_level3.append(team)
            # for team in self.relegated_teams_level3:
            #     self.teams_level3.remove(team)
            #     self.teams_level4.append(team)
            # for team in self.promoted_teams_level4:
            #     self.teams_level3.append(team)
            #     self.teams_level4.remove(team)
        
        return True

    def get_mean_rating(self, rating_name, season, level, default_rating):
        ratings_list = []
        team_ids = [team_id for team_id, seasons in self.teams_level.items() if season in seasons.keys() and seasons[season]== level]
        for t in team_ids:
            last_season_rating = self.data.nodes[t].get('ratings', {}).get(rating_name, {}).get(season, 0)[-1]
            ratings_list.append(last_season_rating)
        return default_rating[0] if len(ratings_list) == 0 else np.mean(ratings_list)

class InternationalCompetition_Combine:
    def __init__(self, **kwargs):
        """
        InternationalCompetition class
        """
        self.countries_configs = kwargs.get('countries_configs', {})
        self.international_prob = kwargs.get('match_prob', 0.1)
        self.oneleg = kwargs.get('oneleg', False)
        self.teams_per_country = kwargs.get('teams_per_country', 3)
        self.countries_leagues = {}
        self.seasons = kwargs.get('seasons', 1)
        
        self.team_id_map = {}  # map from original team id to new unique team id
        self.selected_teams_list = []
        self.team_level_map = {}
        self.true_forecast = kwargs.get(
            'true_forecast',
            LogFunctionForecast(
                outcomes=['home', 'draw', 'away'],
                coefficients=[-0.9, 0.3],
                beta_parameter=0.006
            )
        )
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
        
        # merge country graphs
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
                

        self.international_teams_list = {}
        
        # add international competition at next of each season
        for season in range(self.seasons):
            print('international competitinon after season: ', season)
            
            # choose each country's teams
            self.international_teams_list[season] = []
            for country_idx, country_league in self.countries_leagues.items():
                clusters = [team for team,seasons in country_league.teams_level.items() if seasons[season] == 'level1']
                selected_teams = country_league.select_teams(clusters, self.teams_per_country, season, 'random')
                for t in selected_teams:
                    self.international_teams_list[season].append(country_node_mapping[country_idx][t])
                print(f'teams from country {country_idx}: {selected_teams}')
            
            ###### add edges between selected teams
            if season == 0:
                continue
            teams_list = self.international_teams_list[season-1]
            number_of_teams = len(teams_list)
            n_games_per_round = int(math.ceil(number_of_teams / 2))
            number_of_rounds = number_of_teams - 1 + number_of_teams % 2
            
            team_labels = {i:i for i in teams_list}

            graph = self.data

            if number_of_teams % 2 != 0:
                teams_list.append(-1)
            slice_a = teams_list[0:n_games_per_round]
            slice_b = teams_list[n_games_per_round:]
            fixed = teams_list[0]
            day = 1
            self.days_between_rounds = 1
            for season_round in range(0, number_of_rounds):
                for game in range(0, n_games_per_round):
                    if (slice_a[game] != -1) and (slice_b[game] != -1):
                        if season_round % 2 == 0:
                            graph.add_edge(
                                team_labels.get(slice_a[game], slice_a[game]),
                                team_labels.get(slice_b[game], slice_b[game]),
                                season=season, round=season_round, day=day, competition_type='international'
                            )
                            graph.add_edge(
                                team_labels.get(slice_b[game], slice_b[game]),
                                team_labels.get(slice_a[game], slice_a[game]),
                                season=season, round=season_round + number_of_rounds,
                                day=day + (number_of_rounds * self.days_between_rounds),
                                competition_type='international'
                            )
                        else:
                            graph.add_edge(
                                team_labels.get(slice_b[game], slice_b[game]),
                                team_labels.get(slice_a[game], slice_a[game]),
                                season=season, round=season_round, day=day, competition_type='international'
                            )
                            graph.add_edge(
                                team_labels.get(slice_a[game], slice_a[game]),
                                team_labels.get(slice_b[game], slice_b[game]),
                                season=season, round=season_round + number_of_rounds,
                                day=day + (number_of_rounds * self.days_between_rounds), 
                                competition_type='international'
                            )

                day += self.days_between_rounds
                rotate = slice_a[-1]
                slice_a = [fixed, slice_b[0]] + slice_a[1:-1]
                slice_b = slice_b[1:] + [rotate]

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
            
            print(f'play International Competition Season {season-1}')

            def find_team_id_in_country(country_node_mapping, team_id):
                for country_id, teams in country_node_mapping.items():
                    for original_id, mapped_id in teams.items():
                        if mapped_id == team_id:
                            return country_id, original_id
                return None, None
            # add forecast
            international_match_list = [(u,v,k) for u,v,k,data in self.data.edges(keys=True, data=True) if data['season'] == season and data.get('competition_type','')=='international']
            for match in international_match_list:
                round_pointer = self.data.edges[match].get('round', 0)
                home_team_country, home_team_origin = find_team_id_in_country(country_node_mapping, match[0])
                away_team_country, away_team_origin = find_team_id_in_country(country_node_mapping, match[1])
                home_rating = self.countries_leagues[home_team_country].data.nodes[home_team_origin].get('ratings', {}).get('true_rating', {}).get(season, 0)[round_pointer+1]
                away_rating = self.countries_leagues[away_team_country].data.nodes[away_team_origin].get('ratings', {}).get('true_rating', {}).get(season, 0)[round_pointer+1]
                forecast_object = deepcopy(self.true_forecast)
                diff = forecast_object.home_error.apply(home_rating) - forecast_object.away_error.apply(away_rating)
                for i in range(len(forecast_object.outcomes)):
                    n = len(forecast_object.outcomes)
                    j = i+1
                    forecast_object.probabilities[i]=forecast_object.logit_link_function(n-j+1,diff)-forecast_object.logit_link_function(n-j,diff)
                forecast_object.computed = True
                self.data.edges[match].setdefault('forecasts', {})['true_forecast'] = forecast_object

            # play international games
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
    
    def export(self, **kwargs):
        print("Export network")
        network_flat = []
        printing_forecasts = kwargs.get("forecasts", ['true_forecast'])
        printing_ratings = kwargs.get("ratings", ['true_rating'])
        printing_odds = kwargs.get("odds", [])
        printing_bets = kwargs.get("bets", [])
        printing_metrics = kwargs.get("metrics", [])
        for away_team, home_team, edge_key, edge_attributes in self.data.edges(keys=True, data=True):
            match_dict = {
                "Home": home_team,
                "Away": away_team,
                "Season": edge_attributes.get('season', 0),
                "Round": edge_attributes.get('round', -1),
                "Day": edge_attributes.get('day', -1),
                "Result": edge_attributes.get('winner', 'none'),
                "state": edge_attributes.get('state', 'active'),
                'competition_type': edge_attributes.get('competition_type', 'League')
            }
            for f in printing_forecasts:
                forecast_object: BaseForecast = edge_attributes.get('forecasts', {}).get(f, None)
                if forecast_object is not None:
                    for i, outcome in enumerate(forecast_object.outcomes):
                        match_dict[f"{f}#{outcome}"] = forecast_object.probabilities[i]
            for r in printing_ratings:
                for team, name in [(home_team, 'Home'), (away_team, 'Away')]:
                    rating_dict = self.data.nodes[team].get('ratings', {}).get(r)
                    match_dict[f"{r}#{name}"] = rating_dict.get(edge_attributes.get('season', 0))[
                        edge_attributes.get('round', 0)]
            for o in printing_odds:
                for i, value in enumerate(edge_attributes.get('odds', {}).get(o, [])):
                    match_dict[f"{o}#odds#{i}"] = value
            for b in printing_bets:
                for i, value in enumerate(edge_attributes.get('bets', {}).get(b, [])):
                    match_dict[f"{b}#bets#{i}"] = value
            for m in printing_metrics:
                match_dict[f"{m}#metric"] = edge_attributes.get('metrics', {}).get(m, -1)
            network_flat.append(match_dict)
        file_name = kwargs.get('filename', 'network.csv')
        df = pd.DataFrame(network_flat)
        df.to_csv(file_name, index=False)


class InternationalNetwork_small:
    def __init__(self, **kwargs):
        """
        InternationalCompetition class
        """
        self.countries_configs = kwargs.get('countries_configs', {})
        self.international_prob = kwargs.get('match_prob', 0.1)
        self.oneleg = kwargs.get('oneleg', False)
        self.teams_per_country = kwargs.get('teams_per_country', 3)
        self.countries_leagues = {}
        self.seasons = kwargs.get('seasons', 1)
        
        self.team_id_map = {}  # map from original team id to new unique team id
        self.selected_teams_list = []
        self.team_level_map = {}
        
        # generate all countries data
        for country_idx, country_config in self.countries_configs.items():
            print('country:', country_idx)
            country_config['seasons'] = self.seasons
            country_league = CountryLeague(**country_config)
            self.countries_leagues[country_idx] = country_league

        self.international_teams = {}
        for season in range(self.seasons):
            # choose each country's teams
            self.international_teams[season] = []
            for country_idx, country_league in self.countries_leagues.items():
                clusters = [team for team,seasons in country_league.teams_level.items() if seasons[season] == 'level1']
                selected_teams = country_league.select_teams(clusters, self.teams_per_country, season, 'random')
                self.international_teams[season].extend(selected_teams)

            ###### fill graph
            self.International_graph = nx.MultiDiGraph()
            for season, teams in self.international_teams.items():
                self.International_graph.add_nodes_from(teams)
                for i, team1 in enumerate(teams):
                    for team2 in teams[i+1:]:
                        if nx.utils.uniform() < self.international_prob:
                            self.International_graph.add_edge(team1, team2, season=season)
                            if not self.oneleg:
                                self.International_graph.add_edge(team2, team1, season=season)

        Internationa_graph = nx.MultiDiGraph()


class InternationalCompetition(RoundRobinNetwork):
    def __init__(self, **kwargs):
        """
        InternationalCompetition class
        """
        self.countries_configs = kwargs.get('countries_configs', {})
        self.international_prob = kwargs.get('international_prob', 0.1)
        self.oneleg_international = kwargs.get('oneleg', False)
        self.teams_per_country = kwargs.get('teams_per_country', 3)
        self.countries_leagues = {}
        self.n_teams = 0
        for country_idx, country_config in self.countries_configs.items():
            self.countries_leagues[country_idx] = country_config
            setattr(self, f'oneleg_{country_idx}', country_config.get('oneleg', False))
            setattr(self, f'number_teams_level1_{country_idx}', country_config.get('level1_teams', 0))
            setattr(self, f'number_teams_level2_{country_idx}', country_config.get('level2_teams', 0))
            setattr(self, f'number_teams_level3_{country_idx}', country_config.get('level3_teams', 0))
            setattr(self, f'n_teams_{country_idx}', getattr(self, f'number_teams_level1_{country_idx}') + getattr(self, f'number_teams_level2_{country_idx}') + getattr(self, f'number_teams_level3_{country_idx}'))
            self.n_teams += getattr(self, f'n_teams_{country_idx}')
            
            setattr(self, f'promotion_number_{country_idx}', country_config.get('promotion_number', 1))
            setattr(self, f'prob_within_level1_{country_idx}', country_config.get('prob_within_level1', 0.7))
            setattr(self, f'prob_within_level2_{country_idx}', country_config.get('prob_within_level2', 0.6))
            setattr(self, f'prob_within_level3_{country_idx}', country_config.get('prob_within_level3', 0.5))
            setattr(self, f'prob_level1_level2_{country_idx}', country_config.get('prob_level1_level2', 0.4))
            setattr(self, f'prob_level1_level3_{country_idx}', country_config.get('prob_level1_level3', 0.3))
            setattr(self, f'prob_level2_level3_{country_idx}', country_config.get('prob_level2_level3', 0.2))
            setattr(self, f'team_labels_{country_idx}', country_config.get('team_labels', None))
            
            setattr(self,f'true_rating_level1_{country_idx}', kwargs.get(
                'true_rating_level1',
                ControlledTrendRating(
                    starting_point=ControlledRandomFunction(distribution='normal', loc=1000, scale=50),
                    delta=ControlledRandomFunction(distribution='normal', loc=0, scale=.5),
                    trend=ControlledRandomFunction(distribution='normal', loc=0, scale=.2),
                    season_delta=ControlledRandomFunction(distribution='normal', loc=0, scale=30),
                    rating_name='true_rating'
                )
            )
            )

            setattr(self,f'true_rating_level2_{country_idx}', kwargs.get(
                'true_rating_level2',
                ControlledTrendRating(
                    starting_point=ControlledRandomFunction(distribution='normal', loc=800, scale=50),
                    delta=ControlledRandomFunction(distribution='normal', loc=0, scale=.5),
                    trend=ControlledRandomFunction(distribution='normal', loc=0, scale=.2),
                    season_delta=ControlledRandomFunction(distribution='normal', loc=0, scale=30),
                    rating_name='true_rating'
                )
            )
            )

            setattr(self,f'true_rating_level3_{country_idx}', kwargs.get(
                'true_rating_level3',
                ControlledTrendRating(
                    starting_point=ControlledRandomFunction(distribution='normal', loc=500, scale=50),
                    delta=ControlledRandomFunction(distribution='normal', loc=0, scale=.5),
                    trend=ControlledRandomFunction(distribution='normal', loc=0, scale=.2),
                    season_delta=ControlledRandomFunction(distribution='normal', loc=0, scale=30),
                    rating_name='true_rating'
                )
            )
            )
            
            setattr(self,f'true_forecast_{country_idx}', kwargs.get(
                'true_forecast',
                LogFunctionForecast(
                    outcomes=['home', 'draw', 'away'],
                    coefficients=[-0.9, 0.3],
                    beta_parameter=0.006
                )
            )
            )

            setattr(self,f'ranking_rating_{country_idx}', kwargs.get('ranking_rating', LeagueRating()))

        kwargs['teams'] = self.n_teams
        kwargs['play'] = False

        super().__init__(**kwargs)
    
    def fill_graph(self, season=0):
        teams_list = list(range(0, self.n_teams))
        self.team_labels = {i: i for i in range(self.n_teams)}
        if self.data is None:
            graph = nx.MultiDiGraph()
            graph.add_nodes_from([t for t in teams_list])
            self.data = graph
        super().fill_graph(self.team_labels, season)

        team_idx = 0
        for country_idx in range(self.countries_configs):
            teams_list_country = random.sample(teams_list, getattr(self, f'n_teams_{country_idx}'))
            if season == 0:
                setattr(self, f'teams_level1_{country_idx}', random.sample(teams_list_country, getattr(self, f'number_teams_level1_{country_idx}')))
                teams_list_country = [t for t in teams_list_country if t not in getattr(self, f'teams_level1_{country_idx}')]
                setattr(self, f'teams_level2_{country_idx}', random.sample(teams_list_country, getattr(self, f'number_teams_level2_{country_idx}')))
                teams_list_country = [t for t in teams_list_country if t not in getattr(self, f'teams_level2_{country_idx}')]
                setattr(self, f'teams_level3_{country_idx}', teams_list_country)

                setattr(self, f'teams_rating_level1_{country_idx}', getattr(self, f'teams_level1_{country_idx}').copy())
                setattr(self, f'teams_rating_level2_{country_idx}', getattr(self, f'teams_level2_{country_idx}').copy())
                setattr(self, f'teams_rating_level3_{country_idx}', getattr(self, f'teams_level3_{country_idx}').copy())
            print('country:', country_idx)
            print('level1:',getattr(self, f'teams_level1_{country_idx}'))
            print('level2:',getattr(self, f'teams_level2_{country_idx}'))
            print('level3:',getattr(self, f'teams_level3_{country_idx}'))

        def set_edge_state(team1, team2, prob, season):
            def search_edge(team1, team2, season):
                return next(((u, v, key) for u, v, key, data in self.data.edges(keys=True, data=True) if data['season'] == season and u == team1 and v == team2), None)

            edges_team1_2 = search_edge(team1, team2, season)
            if edges_team1_2:
                u, v, key = edges_team1_2
                if not self.oneleg:
                    self.data.edges[u, v, key]['state'] = 'active' if random.random() < prob else 'inactive'
                    self.data.edges[v, u, key]['state'] = 'active' if random.random() < prob else 'inactive'
                else:
                    if random.random() < 0.5:
                        self.data.edges[u, v, key]['state'] = 'active' if random.random() < prob else 'inactive'
                        self.data.edges[v, u, key]['state'] = 'inactive'
                    else:
                        self.data.edges[v, u, key]['state'] = 'active' if random.random() < prob else 'inactive'
                        self.data.edges[u, v, key]['state'] = 'inactive'
        
        for team1 in getattr(self, f'teams_level1_{country_idx}'):
            for team2 in getattr(self, f'teams_level2_{country_idx}'):
                set_edge_state(team1,team2,getattr(self, f'prob_level1_level2_{country_idx}'),season)
        
        for team1 in getattr(self, f'teams_level1_{country_idx}'):
            for team2 in getattr(self, f'teams_level3_{country_idx}'):
                set_edge_state(team1,team2,getattr(self, f'prob_level1_level3_{country_idx}'),season)
        
        for team1 in getattr(self, f'teams_level2_{country_idx}'):
            for team2 in getattr(self, f'teams_level3_{country_idx}'):
                set_edge_state(team1,team2,getattr(self, f'prob_level2_level3_{country_idx}'),season)

    def create_data(self):
        for season in range(self.seasons):
            self.fill_graph(season)
            for country_idx in range(self.countries_configs):
                print('--------------- country:', country_idx, '----------------')
                # add each level's rating
                for level in ['level1','level2','level3']:
                    def edge_filter(e):
                        return e[3]['season'] == season
                    rating_values, rating_hp = getattr(self, f'true_rating_{level}_{country_idx}').get_cluster_ratings(
                    self, getattr(self, f'teams_rating_{level}_{country_idx}'), edge_filter, season
                    )
                    for team in getattr(self, f'teams_rating_{level}_{country_idx}'):
                        # rating_values, rating_hp = rating.get_cluster_ratings(
                        #     self, [team], edge_filter
                        # ) # can give a list of teams
                        index_of_team = getattr(self,f'teams_rating_{level}_{country_idx}').index(team)
                        self._add_rating_to_team(team, rating_values[index_of_team], rating_hp, 'true_rating', season=season)
                        print('team:',team, 'rating_start:',rating_values[index_of_team][0])
                self.add_forcast(getattr(self, f'true_forecast_{country_idx}'), 'true_forecast', season=season)
                season_games = list(filter(lambda match: match[3].get('season', -1) == season, self.iterate_over_games()))