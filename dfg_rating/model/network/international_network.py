import random
import networkx as nx
import numpy as np
from networkx import DiGraph
from dfg_rating.model.network.simple_network import RoundRobinNetwork
from dfg_rating.model.network.base_network import BaseNetwork
import math
from dfg_rating.model.forecast.true_forecast import LogFunctionForecast
from dfg_rating.model.rating.controlled_trend_rating import ControlledTrendRating, ControlledRandomFunction



class CountryLeague(RoundRobinNetwork):
    def __init__(self, **kwargs):
        # self.num_teams = kwargs.get('teams', 24)
        self.oneleg = kwargs.get('oneleg', False)
        self.num_teams_level1 = kwargs.get('level1_teams', 10)
        self.num_teams_level2 = kwargs.get('level2_teams', 8)
        self.num_teams_level3 = kwargs.get('level3_teams', 6)
        # self.rating_params = {
        #     'level1': kwargs.get('level1_rating', 1000),
        #     'level2': kwargs.get('level2_rating', 800),
        #     'level3': kwargs.get('level3_rating', 600)
        # }
        self.prob_within_level1 = kwargs.get('prob_within_level1', 0.7)
        self.prob_within_level2 = kwargs.get('prob_within_level2', 0.6)
        self.prob_within_level3 = kwargs.get('prob_within_level3', 0.5)
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
                rating_name='true_rating_level1'
            )
        )

        self.true_rating_level2 = kwargs.get(
            'true_rating_level2',
            ControlledTrendRating(
                starting_point=ControlledRandomFunction(distribution='normal', loc=800, scale=50),
                delta=ControlledRandomFunction(distribution='normal', loc=0, scale=.5),
                trend=ControlledRandomFunction(distribution='normal', loc=0, scale=.2),
                season_delta=ControlledRandomFunction(distribution='normal', loc=0, scale=30),
                rating_name='true_rating_level2'
            )
        )

        self.true_rating_level3 = kwargs.get(
            'true_rating_level3',
            ControlledTrendRating(
                starting_point=ControlledRandomFunction(distribution='normal', loc=500, scale=50),
                delta=ControlledRandomFunction(distribution='normal', loc=0, scale=.5),
                trend=ControlledRandomFunction(distribution='normal', loc=0, scale=.2),
                season_delta=ControlledRandomFunction(distribution='normal', loc=0, scale=30),
                rating_name='true_rating_level3'
            )
        )

        self.true_forecast = kwargs.get(
            'true_forecast',
            LogFunctionForecast(
                outcomes=['home', 'draw', 'away'],
                coefficients=[-0.9, 0.3],
                beta_parameter=0.006
            )
        )
        super().__init__(**kwargs)
    

    def fill_graph(self, season=0):

        if self.team_labels is None:
            teams_list = list(range(0, self.n_teams))
        else:
            teams_list = list(self.team_labels.keys())
        if self.data is None:
            graph = nx.MultiDiGraph()
            graph.add_nodes_from([t for t in teams_list])
            self.data = graph
        super().fill_graph(self.team_labels, season)

        
        # get 3 level's team idx
        
        self.teams_level1 = random.sample(teams_list, self.num_teams_level1)
        teams_list = [t for t in teams_list if t not in self.teams_level1]
        self.teams_level2 = random.sample(teams_list, self.num_teams_level2)
        teams_list = [t for t in teams_list if t not in self.teams_level2]
        self.teams_level3 = teams_list
        print('level1:',self.teams_level1)
        print('level2:',self.teams_level2)
        print('level3:',self.teams_level3)


        def set_edge_state(team1, team2, prob):
            if not self.oneleg:
                self.data.edges[team2, team1, 0]['state'] = 'active' if random.random() < prob else 'inactive'
                self.data.edges[team1, team2, 0]['state'] = 'active' if random.random() < prob else 'inactive'
            else:
                if random.random() < 0.5:
                    self.data.edges[team1, team2, 0]['state'] = 'active' if random.random() < prob else 'inactive'
                    self.data.edges[team2, team1, 0]['state'] = 'inactive'
                else:
                    self.data.edges[team2, team1, 0]['state'] = 'active' if random.random() < prob else 'inactive'
                    self.data.edges[team1, team2, 0]['state'] = 'inactive'
        
        # # Generate matches within each level
        # for level in ['level1','level2','level3']:
        #     for team1 in getattr(self, f'teams_{level}'):
        #         for team2 in getattr(self, f'teams_{level}'):
        #             if team1 != team2:
        #                 self.data.edges[team1,team2,0]['state'] = 'active' if random.random() < getattr(self, f'prob_within_{level}') else 'inactive'
        #                 # if not self.oneleg: # league cup is two leg
        #                 self.data.edges[team2,team1,0]['state'] = 'active' if random.random() < getattr(self, f'prob_within_{level}') else 'inactive'

        # Generate matches between different levels
        for team1 in self.teams_level1:
            for team2 in self.teams_level2:
                set_edge_state(team1,team2,self.prob_level1_level2)

        for team1 in self.teams_level1:
            for team2 in self.teams_level3:
                set_edge_state(team1,team2,self.prob_level1_level3)

        for team1 in self.teams_level2:
            for team2 in self.teams_level3:
                set_edge_state(team1,team2,self.prob_level2_level3)
    
    # def add_season_rating(self, rating, rating_name, season):
    #     def edge_filter(e):
    #         return e[3]['season'] == season
        
    #     # add rating to all teams

    #     rating_values, rating_hp = rating.get_cluster_ratings(
    #         self, getattr(self, f'teams_{level}'), edge_filter
    #     )
    #     for team in getattr(self, f'teams_{level}'):
    #         # rating_values, rating_hp = rating.get_cluster_ratings(
    #         #     self, [team], edge_filter
    #         # ) # can give a list of teams
    #         index_of_team = getattr(self,f'teams_{level}').index(team)
    #         self._add_rating_to_team(team, rating_values[index_of_team], rating_hp, rating_name, season=season) # only one by one
    #         print('team:',team, 'rating_start:',rating_values[index_of_team][0])
        
    def create_data(self):
        # fill the country graph
        self.fill_graph()

        # add each level's rating
        for level in ['level1','level2','level3']:
            season = 0
            def edge_filter(e):
                return e[3]['season'] == season
            rating_values, rating_hp = getattr(self, f'true_rating_{level}').get_cluster_ratings(
            self, getattr(self, f'teams_{level}'), edge_filter
            )
            for team in getattr(self, f'teams_{level}'):
                # rating_values, rating_hp = rating.get_cluster_ratings(
                #     self, [team], edge_filter
                # ) # can give a list of teams
                index_of_team = getattr(self,f'teams_{level}').index(team)
                self._add_rating_to_team(team, rating_values[index_of_team], rating_hp, 'true_rating', season=season) # only one by one
                print('team:',team, 'rating_start:',rating_values[index_of_team][0])
        
            # self.add_season_rating(getattr(self, f'true_rating_{level}'), f'true_rating', season=0)
        
        # add forecast to all games
        super().add_forecast(self.true_forecast, 'true_forecast')
        
        return True
        
class InternationalCompetition:
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

