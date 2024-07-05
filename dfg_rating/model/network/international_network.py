import random
import networkx as nx
import numpy as np
from networkx import DiGraph
from dfg_rating.model.network.simple_network import RoundRobinNetwork
from dfg_rating.model.network.random_network import ClusteredNetwork
import dfg_rating.viz.jupyter_widgets as DFGWidgets
import math
import matplotlib.pyplot as plt
from copy import deepcopy


class CountryLeague(RoundRobinNetwork):
    def __init__(self, **kwargs):
        # self.num_teams = kwargs.get('teams', 24)
        self.oneleg = kwargs.get('oneleg', False)
        self.num_teams_level1 = kwargs.get('level1_teams', 10)
        self.num_teams_level2 = kwargs.get('level2_teams', 8)
        self.num_teams_level3 = kwargs.get('level3_teams', 6)
        self.rating_params = {
            'level1': kwargs.get('level1_rating', 1000),
            'level2': kwargs.get('level2_rating', 800),
            'level3': kwargs.get('level3_rating', 600)
        }
        self.prob_within_level1 = kwargs.get('prob_within_level1', 0.7)
        self.prob_within_level2 = kwargs.get('prob_within_level2', 0.6)
        self.prob_within_level3 = kwargs.get('prob_within_level3', 0.5)
        self.prob_level1_level2 = kwargs.get('prob_level1_level2', 0.4)
        self.prob_level1_level3 = kwargs.get('prob_level1_level3', 0.3)
        self.prob_level2_level3 = kwargs.get('prob_level2_level3', 0.2)
        
        super().__init__(**kwargs)

    

    def fill_graph(self, team_labels=None, season=0):
        super().fill_graph(team_labels, season)
        
        # get 3 level's team idx
        teams_list = list(range(0, self.n_teams))
        self.teams_level1 = random.sample(teams_list, self.num_teams_level1)
        teams_list = [t for t in teams_list if t not in self.teams_level1]
        self.teams_level2 = random.sample(teams_list, self.num_teams_level2)
        teams_list = [t for t in teams_list if t not in self.teams_level2]
        self.teams_level3 = teams_list

        # self.teams_level1 = teams_list[0:self.num_teams_level1]
        # self.teams_level2 = teams_list[self.num_teams_level1:self.num_teams_level1+self.num_teams_level2]
        # self.teams_level3 = teams_list[self.num_teams_level1+self.num_teams_level2:]

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
        
class InternationalCompetition(RoundRobinNetwork):
    def __init__(self, countries_config, teams_per_country=3, match_prob=0.5, **kwargs):
        """
        InternationalCompetition class
        """
        self.countries = []
        self.teams_per_country = teams_per_country
        self.match_prob = match_prob
        
        self.team_id_map = {}  # map from original team id to new unique team id
        self.selected_teams = []
        team_id_offset = 0

        # Initialize CountryLeague instances and collect teams
        for country_index, country_config in enumerate(countries_config):
            country_league = CountryLeague(**country_config)
            self.countries.append(country_league)
            
            # Collect teams and assign unique ids
            selected = random.sample(country_league.teams_level1, min(self.teams_per_country, len(country_league.teams_level1)))
            for team_id in country_league.teams_level1:
                new_team_id = team_id_offset
                self.team_id_map[(country_index, team_id)] = new_team_id
                if team_id in selected:
                    self.selected_teams.append(new_team_id)
                team_id_offset += 1
        
        super().__init__(**kwargs)
    
    def select_from_1level(self, country_index, n):
        country = self.countries[country_index]
        return random.sample(country.teams_level1, n)
    
    def fill_graph(self, team_labels=None, season=0):
        if team_labels is None:
            team_labels = {v: k for k, v in self.team_id_map.items()}
        
        graph = nx.MultiDiGraph()

        # Add nodes and edges for each country
        for country_index, country in enumerate(self.countries):
            for team_id in country.teams_level1 + country.teams_level2 + country.teams_level3:
                new_team_id = self.team_id_map[(country_index, team_id)]
                graph.add_node(new_team_id)
                
                for opponent_id in country.teams_level1 + country.teams_level2 + country.teams_level3:
                    if team_id != opponent_id:
                        new_opponent_id = self.team_id_map[(country_index, opponent_id)]
                        active = random.random() < getattr(country, f'prob_within_level{country.get_level(team_id)}')
                        graph.add_edge(new_team_id, new_opponent_id, state='active' if active else 'inactive')
                        graph.add_edge(new_opponent_id, new_team_id, state='active' if active else 'inactive')
        
        # Add edges for international competition
        def set_edge_state(team1, team2, prob):
            active = random.random() < prob
            graph.add_edge(team1, team2, state='active' if active else 'inactive')
            graph.add_edge(team2, team1, state='active' if active else 'inactive')

        for i, team1 in enumerate(self.selected_teams):
            for j, team2 in enumerate(self.selected_teams):
                if i != j:
                    set_edge_state(team1, team2, self.match_prob)
        
        self.data = graph
        self.network_info.setdefault(str(season), {})["teams_playing"] = team_labels




country1 = CountryLeague(
    teams=10,
    level1_teams=4,
    level2_teams=4,
    level3_teams=2,
    # level1_rating=1000,
    # level2_rating=800,
    # level3_rating=600,
    prob_within_level1=1.0,
    prob_within_level2=1.0,
    prob_within_level3=1.0,
    prob_level1_level2=0.1,
    prob_level1_level3=0.05,
    prob_level2_level3=0.1,
    oneleg=True
)

# Display the network to verify the structure
app = DFGWidgets.NetworkExplorer(
    network=country1,
    edge_props=["round"]
)
app.run('internal', debug=True, port=8001)


countries_config = [
    {
        'teams': 10,
        'level1_teams': 4,
        'level2_teams': 4,
        'level3_teams': 2,
        'prob_within_level1': 1.0,
        'prob_within_level2': 1.0,
        'prob_within_level3': 1.0,
        'prob_level1_level2': 0.00,
        'prob_level1_level3': 0.00,
        'prob_level2_level3': 0.00,
        'oneleg': True
    },
    {
        'teams': 10,
        'level1_teams': 4,
        'level2_teams': 4,
        'level3_teams': 2,
        'prob_within_level1': 1.0,
        'prob_within_level2': 1.0,
        'prob_within_level3': 1.0,
        'prob_level1_level2': 0.00,
        'prob_level1_level3': 0.00,
        'prob_level2_level3': 0.00,
        'oneleg': True
    }
]

international_competition = InternationalCompetition(
    countries_config=countries_config,
    teams_per_country=3,
    match_prob=0.5
)