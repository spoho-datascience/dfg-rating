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


class CountryLeague(RoundRobinNetwork):
    def __init__(self, **kwargs):
        self.oneleg = kwargs.get('oneleg', True)
        self.num_teams_level1 = kwargs.get('level1_teams', 12)
        self.num_teams_level2 = kwargs.get('level2_teams', 12)
        self.num_teams_level3 = kwargs.get('level3_teams', 12)
        self.promotion_number = kwargs.get('promotion_number', 2)
        self.n_teams = kwargs.get('teams', 0)
        self.n_playing = self.num_teams_level1 + self.num_teams_level2 + self.num_teams_level3
        kwargs['teams'] = self.n_teams
        kwargs['play'] = False
        

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
                starting_point=ControlledRandomFunction(distribution='normal', loc=800, scale=50),
                delta=ControlledRandomFunction(distribution='normal', loc=0, scale=.5),
                trend=ControlledRandomFunction(distribution='normal', loc=0, scale=.2),
                season_delta=ControlledRandomFunction(distribution='normal', loc=0, scale=30),
                rating_name='true_rating'
            )
        )

        self.true_rating_level3 = kwargs.get(
            'true_rating_level3',
            ControlledTrendRating(
                starting_point=ControlledRandomFunction(distribution='normal', loc=500, scale=50),
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
        if isinstance(clusters[0], list):
            selected_teams = [select_from_cluster(cluster, select_n_teams, selection_strategy) for cluster in clusters]
        else:
            selected_teams = select_from_cluster(clusters, select_n_teams, selection_strategy)
        # selected_teams_1 = random.sample(cluster_1, select_n_teams) if select_n_teams else cluster_1
        # selected_teams_2 = random.sample(cluster_2, select_n_teams) if select_n_teams else cluster_2

        # if set_edge_state:
        #     for i, cluster_1 in enumerate(selected_teams):
        #         for cluster_2 in selected_teams[i+1:]:
        #             for team1 in cluster_1:
        #                 for team2 in cluster_2:
        #                     self.set_edge_state(team1, team2, prob, season)
            # for team1 in selected_teams_1:
            #     for team2 in selected_teams_2:
            #         self.set_edge_state(team1, team2, prob, season)

        # else:
        return selected_teams
    
    def initiate_3_levels(self, team_list, n_teams_level1, n_teams_level2, n_teams_level3):
        teams_level1 = random.sample(team_list, n_teams_level1)
        teams_list = [t for t in team_list if t not in teams_level1]
        teams_level2 = random.sample(teams_list, n_teams_level2)
        teams_list = [t for t in teams_list if t not in teams_level2]
        teams_level3 = random.sample(teams_list, n_teams_level3)
        teams_level4 = [t for t in teams_list if t not in teams_level3]
        return teams_level1, teams_level2, teams_level3, teams_level4
    
    def set_edge_state(self, team1, team2, prob, season):
        def search_edge(team1, team2, season):
            return next(((u, v, key) for u, v, key, data in self.data.edges(keys=True, data=True) if data['season'] == season and u == team1 and v == team2), None)

        edges_team1_2 = search_edge(team1, team2, season)
        if edges_team1_2:
            u, v, key = edges_team1_2
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
            # self.teams_level1, self.teams_level2, self.teams_level3, self.teams_level4 = self.initiate_3_levels(teams_list, self.num_teams_level1, self.num_teams_level2, self.num_teams_level3)
            self.teams_rating_level1 = self.teams_level1.copy()
            self.teams_rating_level2 = self.teams_level2.copy()
            self.teams_rating_level3 = self.teams_level3.copy()
            self.teams_rating_level4 = self.teams_level4.copy()

        print('level1:',self.teams_level1)
        print('level2:',self.teams_level2)
        print('level3:',self.teams_level3)


        clusters_probabilities = [
            (self.teams_level1, self.teams_level2, self.prob_level1_level2),
            (self.teams_level1, self.teams_level3, self.prob_level1_level3),
            (self.teams_level2, self.teams_level3, self.prob_level2_level3),
            (self.teams_level1, self.teams_level4, 0),
            (self.teams_level2, self.teams_level4, 0),
            (self.teams_level3, self.teams_level4, 0),
            (self.teams_level4, self.teams_level4, 0)
        ]

        for cluster1, cluster2, prob in clusters_probabilities:
            # selected_teams = self.select_teams([cluster1, cluster2], season)
            selected_teams = [cluster1, cluster2] # dont need select
            for team1 in selected_teams[0]:
                for team2 in selected_teams[1]:
                    self.set_edge_state(team1, team2, prob, season)
        

        # for i in [1,2,3]:
        #     for j in [2,3]:
        #         if i != j and i<j:
        #             cluster_1 = getattr(self, f'teams_level{i}')
        #             cluster_2 = getattr(self, f'teams_level{j}')
        #             prob = getattr(self, f'prob_level{i}_level{j}')
        #             self.select_teams(cluster_1, cluster_2, prob, season, set_edge_state=True)
        #     cluster_1 = getattr(self, f'teams_level{i}')
        #     cluster_2 = getattr(self, 'teams_level4')
        #     self.select_teams(cluster_1, cluster_2, 0, season, set_edge_state=True)
        
        # self.select_teams(self.teams_level4, self.teams_level4, 0, season, set_edge_state=True)

    def create_data(self):
        for season in range(self.seasons):
            print('--------------- season:', season, '----------------')
            # season = 0
            
            # fill the country graph
            self.fill_graph(season=season)

            # add each level's rating
            for level in ['level1','level2','level3', 'level4']:
                def edge_filter(e):
                    return e[3]['season'] == season
                rating_values, rating_hp = getattr(self, f'true_rating_{level}').get_cluster_ratings(
                self, getattr(self, f'teams_rating_{level}'), edge_filter, season
                )
                for team in getattr(self, f'teams_rating_{level}'):
                    index_of_team = getattr(self,f'teams_rating_{level}').index(team)
                    self._add_rating_to_team(team, rating_values[index_of_team], rating_hp, 'true_rating', season=season) # only one by one
                    print('team:',team, 'rating_start:',rating_values[index_of_team][0])
            
            
            # add forecast to all games
            super().add_forecast(self.true_forecast, 'true_forecast', season=season)
            # play this season
            season_games = list(filter(lambda match: match[3].get('season', -1) == season, self.iterate_over_games()))
            self.play_sub_network(season_games)
            print('********** playing season:', season, '*********')
            # based on the reslut of game, give ranking
            for level in ['level1','level2','level3', 'level4']:
                print('*******', level)
                ratings, rating_hp = self.ranking_rating.get_cluster_ratings(self, getattr(self, f'teams_{level}'), season=season, level=level)
                for team in getattr(self, f'teams_{level}'):
                    index_of_team = getattr(self,f'teams_{level}').index(team)
                    self._add_rating_to_team(team, ratings[index_of_team], rating_hp, 'ranking', season=season)
                    print('team:',team, 'ranking_end_season:',ratings[index_of_team][-1])
                # self.add_rating(self.ranking_rating, 'ranking', getattr(self, f'teams_{level}'), season=season)

            # get promoted and relegated teams based on ranking
            for level in ['level1','level2','level3','level4']:
                promote = self.select_teams(getattr(self, f'teams_{level}'), self.promotion_number, season=season, selection_strategy='top')
                relegate = self.select_teams(getattr(self, f'teams_{level}'), self.promotion_number, season=season, selection_strategy='bottom')
                setattr(self, f'promoted_teams_{level}', promote)
                setattr(self, f'relegated_teams_{level}', relegate)

                # season_round = self.n_rounds
                # teams_with_ranking = {}
                # # set_of_nodes = [node for node in self.data.nodes if node in list(self.teams_level1)]
                # for node in getattr(self, f'teams_{level}'):
                #     try:
                #         # I think should choose the last ranking of the season
                #         teams_with_ranking[node]=self.data.nodes[node].get('ratings', {}).get('ranking', {}).get(season, {})[-1]
                #     except KeyError as K:
                #         pass
                # sorted_teams = sorted(teams_with_ranking.items(), key=lambda item: item[1])
                # top_ranking = [key for key, value in sorted_teams[-self.promotion_number:]]
                # tail_ranking = [key for key, value in sorted_teams[:self.promotion_number]]
                # setattr(self, f'promoted_teams_{level}', top_ranking)
                # setattr(self, f'relegated_teams_{level}', tail_ranking)

            for team in self.promoted_teams_level2:
                self.teams_level1.append(team)
                self.teams_level2.remove(team)
            for team in self.relegated_teams_level1:
                self.teams_level1.remove(team)
                self.teams_level2.append(team)
            for team in self.promoted_teams_level3:
                self.teams_level2.append(team)
                self.teams_level3.remove(team)
            for team in self.relegated_teams_level2:
                self.teams_level2.remove(team)
                self.teams_level3.append(team)
            for team in self.relegated_teams_level3:
                self.teams_level3.remove(team)
                self.teams_level4.append(team)
            for team in self.promoted_teams_level4:
                self.teams_level3.append(team)
                self.teams_level4.remove(team)
        
        return True


class InternationalCompetition_Combine:
    def __init__(self, **kwargs):
        """
        InternationalCompetition class
        """
        self.countries_configs = kwargs.get('countries_configs', {})
        self.international_prob = kwargs.get('international_prob', 0.1)
        self.oneleg = kwargs.get('oneleg', True)
        self.teams_per_country = kwargs.get('teams_per_country', 3)
        self.countries_leagues = {}
        
        self.team_id_map = {}  # map from original team id to new unique team id
        self.selected_teams_list = []
        self.team_level_map = {}
        # generate all countries data
        self.total_teams = 0
        for country_idx, country_config in self.countries_configs.items():
            country_league = CountryLeague(**country_config)
            # self.data = nx.compose(self.data, country_league.data)
            self.countries_leagues[country_idx] = country_league
            self.team_level_map[country_idx] = {'level1': country_league.teams_level1, 'level2': country_league.teams_level2, 'level3': country_league.teams_level3}
            
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

        # update level information and random select teams
        for country_idx, levels in self.team_level_map.items():
            for level, teams in levels.items():
                self.team_level_map[country_idx][level] = [country_node_mapping[country_idx][t] for t in teams]
                if level == 'level1':
                    self.selected_teams_list.append(random.sample(self.team_level_map[country_idx][level], self.teams_per_country))
        
        # edges between countries
        for u in self.selected_teams_list:
            for v in self.selected_teams_list:
                if u != v and not from_same_country(u,v):
                    self.data.add_edge(u, v, round=0, state='active' if random.random() < self.international_prob else 'inactive')
                    if not self.oneleg:
                        self.data.add_edge(v, u, round=0, state='active' if random.random() < self.international_prob else 'inactive')
            
        def from_same_country(u,v):
            for country_idx, teams in self.team_level_map.items():
                if u in teams['level1'] and v in teams['level1']:
                    return True
            return False

    def select_from_1level(self, country_index, n):
        country = self.countries[country_index]
        return random.sample(country.teams_level1, n)
    
    def generate_country_leagues(self):
        pass
    def merge_country_leagues(self):
        pass
    def generate_international_matches(self):
        pass
    def fill_graph(self, team_labels=None, season=0):
        self.generate_country_leagues()
        self.merge_country_leagues()
        self.generate_international_matches()

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