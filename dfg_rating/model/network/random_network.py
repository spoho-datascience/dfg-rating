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


class ConfigurationModelNetwork(RoundRobinNetwork):
    """
    Creates a system network that is mapped into a configuration model network
    without self-loops.
    """

    def __init__(self, **kwargs):
        self.expected_home_matches = kwargs.get("expected_home_matches")
        self.expected_away_matches = kwargs.get("expected_away_matches")
        self.variance_home_matches = kwargs.get("variance_home_matches", 0)
        self.variance_away_matches = kwargs.get("variance_away_matches", 0)
        super().__init__(**kwargs)

    def fill_graph(self, team_labels=None, season=0):
        super().fill_graph(team_labels, season)
        home_sequence = self.create_degree_sequence(self.expected_home_matches, self.variance_home_matches)
        away_sequence = self.create_degree_sequence(
            self.expected_away_matches,
            self.variance_away_matches,
            total_sum=home_sequence.sum()
        )
        directed_conf_model = nx.directed_configuration_model(home_sequence, away_sequence, create_using=DiGraph)
        for match in self.data.edges(keys=True):
            if directed_conf_model.has_edge(match[0], match[1]):
                self.data.edges[match]["state"] = "active"
            else:
                self.data.edges[match]["state"] = "inactive"

    def create_degree_sequence(self, expected, variance, total_sum=None):
        sequence = np.random.default_rng().integers(
            low=expected - variance,
            high=expected + variance + 1,
            size=self.n_teams
        )
        if total_sum is not None:
            while sequence.sum() != total_sum:
                diff = total_sum - sequence.sum()
                random_index = np.random.randint(low=0, high=len(sequence))
                if diff + sequence[random_index] > 0:
                    sequence[random_index] += diff
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



