import math
import networkx as nx

from dfg_rating.model.network.base_network import BaseNetwork
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
        n_teams = self.params.get('number_of_teams', 0)
        n_rounds = self.params.get('rounds', n_teams - 1)
        days_between_rounds = self.params.get('days_between_rounds', 1)
        n_games_per_round = self.params.get('games_per_round', int(math.ceil(n_teams / 2)))

        teams_list = [t for t in range(0, n_teams)]
        if n_teams % 2 != 0:
            teams_list.append(-1)

        slice_a = teams_list[0:n_games_per_round]
        slice_b = teams_list[n_games_per_round:]
        fixed = teams_list[0]

        day = 1
        for season_round in range(0, n_rounds):
            for game in range(0, n_games_per_round):
                if (slice_a[game] != -1) and (slice_b[game] != -1):
                    if season_round % 2 == 0:
                        graph.add_edge(slice_a[game], slice_b[game], round=season_round, day=day)
                    else:
                        graph.add_edge(slice_b[game], slice_a[game], round=season_round, day=day)

            day += days_between_rounds
            rotate = slice_a[-1]
            slice_a = [fixed, slice_b[0]] + slice_a[1:-1]
            slice_b = slice_b[1:] + [rotate]

        self.data = graph
        return True

    def print_data(self):
        print("Network schedule")
        for away_team, home_team, edge_attributes in sorted(self.data.edges.data(), key=lambda t: t[2]['round']):
            print(f"({away_team} -> {home_team} at round {edge_attributes['round']}, day {edge_attributes['day']})")
        print("---------------")
        if 'ratings' in self.data.nodes[0]:
            print("Teams ratings")
            for team in self.data.nodes:
                print(f"Team {team}:")
                for key, value in self.data.nodes[team]['ratings'].items():
                    print(f"Rating {key}: > {value}")

    def _add_rating_to_team(self, team_id, rating_values, rating_name):
        self.data.nodes[team_id]['ratings'] = {}
        self.data.nodes[team_id]['ratings'][rating_name] = rating_values

    def add_rating(self, rating: FunctionRating, team_id, rating_name):
        n_teams = self.params.get('number_of_teams', 0)
        n_rounds = self.params.get('rounds', n_teams - 1)
        if team_id > 0:
            self._add_rating_to_team(team_id, rating.compute_array(n_rounds), rating_name)
        else:
            for team in self.data.nodes:
                self._add_rating_to_team(int(team), rating.compute_array(n_rounds), rating_name)


if __name__ == '__main__':
    print(">> Testing network module in Model package")
    print(">> Testing Simple Network model")
    network = s = RoundRobinNetwork(
        "type",
        {
            "number_of_teams": 5,
            "days_between_rounds": 3
        }
    )
    print(">> Creating network")
    s.create_data()
    print(">> Printing network")
    s.print_data()
    print(">> Creating rating")
    s.add_rating(FunctionRating('normal', 5, 1), -1, 'normal')
    print(">> Printing network")
    s.print_data()
