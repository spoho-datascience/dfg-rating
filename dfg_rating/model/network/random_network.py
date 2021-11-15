import random
import networkx as nx
import numpy as np
from networkx import DiGraph

from dfg_rating.model.network.simple_network import RoundRobinNetwork


class RandomNetwork(RoundRobinNetwork):
    """
    Chooses each of the possible [n(n-1)]/2 edges with probability p.
    """

    def __init__(self, **kwargs):
        self.edge_probability = kwargs.get("edge_probability", 1)
        super().__init__(**kwargs)

    def fill_graph(self, team_labels=None, season=0):
        super().fill_graph(team_labels, season)
        for u in range(self.n_teams):
            for v in range(self.n_teams):
                if u != v:
                    self.data.edges[u, v, 0][
                        'state'] = 'active' if random.random() < self.edge_probability else 'inactive'


class RandomRoundsNetwork(RoundRobinNetwork):

    def __init__(self, **kwargs):
        self.absolute_rounds = kwargs.get("absolute_rounds", 1)
        super().__init__(**kwargs)

    def fill_graph(self, team_labels=None, season=0):
        super().fill_graph(team_labels, season)
        selected_rounds = np.random.choice(self.n_rounds * 2, self.absolute_rounds, replace=False)
        #print("selected rounds: ", selected_rounds)
        for u in range(self.n_teams):
            for v in range(self.n_teams):
                if u != v:
                    edge_round = self.data.edges[u, v, season]['round']
                    self.data.edges[u, v, season][
                        'state'] = 'active' if edge_round in selected_rounds else 'inactive'
        print("Activation of rounds finished")




class ConfigurationModelNetwork(RoundRobinNetwork):
    """
    Creates a system network that is mapped into a configuration model network
    without self-loops.
    """

    def __init__(self, **kwargs):
        self.expected_matches = kwargs.get("expected_matches")
        self.variance_matches = kwargs.get("variance_matches", 0)
        super().__init__(**kwargs)

    def fill_graph(self, team_labels=None, season=0):
        super().fill_graph(team_labels, season)
        degree_sequence = self.create_degree_sequence(self.expected_matches, self.variance_matches)
        print("Seq", degree_sequence)
        directed_conf_model = nx.expected_degree_graph(degree_sequence, selfloops=False)
        for match in self.data.edges(keys=True):
            if directed_conf_model.has_edge(match[0], match[1]):
                self.data.edges[match]["state"] = "active"
            else:
                self.data.edges[match]["state"] = "inactive"

    def create_degree_sequence(self, expected, variance, total_sum=None):
        sequence = np.random.default_rng().integers(
            low=(expected - variance) if expected >= variance else 0,
            high=expected + variance,
            size=self.n_teams
        ) if variance > 0 else np.array([expected] * self.n_teams)
        if total_sum is not None:
            while sequence.sum() != total_sum:
                diff = total_sum - sequence.sum()
                random_index = np.random.randint(low=0, high=len(sequence))
                sequence[random_index] += 1 if diff > 0 else -1
        return sequence


class ClusteredNetwork(RoundRobinNetwork):

    def __init__(self, **kwargs):
        self.number_of_clusters = kwargs.get("clusters", 1)
        self.in_probability = kwargs.get("in_probability", 1.00)
        self.out_probability = kwargs.get("out_probability", 0.5)
        super().__init__(**kwargs)

    def fill_graph(self, team_labels=None, season=0):
        super().fill_graph(team_labels, season)
        for u in range(self.n_teams):
            for v in range(self.n_teams):
                if u != v:
                    u_cluster = u % self.number_of_clusters
                    v_cluster = v % self.number_of_clusters
                    edge_probability = self.in_probability if u_cluster == v_cluster else self.out_probability
                    self.data.edges[u, v, 0][
                        'state'] = 'active' if random.random() < edge_probability else 'inactive'
