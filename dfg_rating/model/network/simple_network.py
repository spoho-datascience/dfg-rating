import math
import networkx as nx

from dfg_rating.model.network.base_network import BaseNetwork
from dfg_rating.model.rating.base_rating import BaseRating
from dfg_rating.model.rating.function_rating import FunctionRating


class RoundRobinNetwork(BaseNetwork):
    """Class that defines a Network modeling a Round-Robin tournamnet (all-play-all tournament).
    A competition in which each contestant meets all other contestants in turn)

    """

    def create_data(self):
        """Propagates data from parameters.
        Updating self.data as the resulting network of matches scheduled.
        Implementing Berger Tables Scheduling algorithm.

        Returns:
            boolean: True if the process has been successful, False if else.
        """
        graph = nx.DiGraph()
        
        n_games_per_round = self.params.get('games_per_round', int(math.ceil(self.n_teams / 2)))

        teams_list = [t for t in range(0, self.n_teams)]
        if self.n_teams % 2 != 0:
            teams_list.append(-1)

        slice_a = teams_list[0:n_games_per_round]
        slice_b = teams_list[n_games_per_round:]
        fixed = teams_list[0]

        day = 1
        for season_round in range(0, self.n_rounds):
            for game in range(0, n_games_per_round):
                if (slice_a[game] != -1) and (slice_b[game] != -1):
                    if season_round % 2 == 0:
                        graph.add_edge(slice_a[game], slice_b[game], round=season_round, day=day)
                        graph.add_edge(slice_b[game], slice_a[game], round=season_round + self.n_rounds, day=day + (self.n_rounds * self.days_between_rounds))
                    else:
                        graph.add_edge(slice_b[game], slice_a[game], round=season_round, day=day)
                        graph.add_edge(slice_a[game], slice_b[game], round=season_round + self.n_rounds, day=day + (self.n_rounds * self.days_between_rounds))

            day += self.days_between_rounds
            rotate = slice_a[-1]
            slice_a = [fixed, slice_b[0]] + slice_a[1:-1]
            slice_b = slice_b[1:] + [rotate]

        self.data = graph
        return True

    def print_data(self, print_schedule=True, print_attributes=True):
        if print_schedule:
            print("Network schedule")
            for away_team, home_team, edge_attributes in sorted(self.data.edges.data(), key=lambda t: t[2]['round']):
                print(f"({away_team} -> {home_team} at round {edge_attributes['round']}, day {edge_attributes['day']})")
                if 'winner' in edge_attributes:
                    print(f"Result: {edge_attributes['winner']}")
            print("---------------")
        if print_attributes:
            if 'ratings' in self.data.nodes[0]:
                print("Teams ratings")
                for team in self.data.nodes:
                    print(f"Team {team}:")
                    for key, value in self.data.nodes[team]['ratings'].items():
                        print(f"Rating {key}: > {value}")

    def iterate_over_games(self):
        return sorted(self.data.edges.data(), key=lambda t: t[2]['round'])

    def _add_rating_to_team(self, team_id, rating_values, rating_name):
        self.data.nodes[team_id]['ratings'] = {}
        self.data.nodes[team_id]['ratings'][rating_name] = rating_values

    def add_rating(self, rating: BaseRating, rating_name, team_id=None):
        self.n_teams = self.params.get('number_of_teams', 0)
        self.n_rounds = self.params.get('rounds', self.n_teams - 1)
        if team_id:
            self._add_rating_to_team(team_id, rating.get_ratings(self, team_id), rating_name)
        else:
            for team in self.data.nodes:
                self._add_rating_to_team(int(team), rating.get_all_ratings(self), rating_name)

