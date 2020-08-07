import random
import networkx as nx

from model.network.base_network import BaseNetwork

import utils.graphs as utils_graphs


class RoundRobinNetwork(BaseNetwork):
    """Class that defines a Network modeling a Round-Robin tournamnet (all-play-all tournament).
    A competition in which each contestant meets all other contestants in turn)

    """

    def create_data(self):
        """Propagates data from parameters.
        Updating self.data as the resulting network of matches scheduled.
        Implementing Berger Tables Scheduling algorithm.

        Returns:
            boolean: True if the process has beens successful, False if else.
        """
        G = nx.DiGraph()
        n_teams = self.params.get('number_of_teams', 0)
        n_rounds = self.params.get('rounds', n_teams - 1)
        n_games_per_round = self.params.get('games_per_round', int(n_teams / 2))

        teams_list = [t for t in range(0, n_teams)]
        if (n_teams % 2 != 0):
            teams_list.append(-1)

        sliceA = teams_list[0:n_games_per_round]
        sliceB = teams_list[n_games_per_round:]
        fixed = teams_list[0]

        for round in range(0, n_rounds):
            game_count = 1
            for game in range(0, n_games_per_round):
                if (sliceA[game] != -1) and (sliceB[game] != -1):
                    if round % 2 == 0:
                        G.add_edge(sliceA[game], sliceB[game], day=round, game=game_count)
                    else:
                        G.add_edge(sliceB[game], sliceA[game], day=round, game=game_count)

                    game_count += 1
            rotate = sliceA[-1]
            sliceA = [fixed, sliceB[0]] + sliceA[1:-1]
            sliceB = sliceB[1:] + [rotate]

        self.data = G
        return True

    def print_data(self):
        for away_team, home_team, day in sorted(self.data.edges(data='day'), key=lambda t: t[2]):
            print(f"({away_team} -> {home_team} at {day})")


if __name__ == '__main__':
    print(">> Testing network module in Model package")
    print(">> Testing Simple Network model")
    network = s = RoundRobinNetwork(
        "type",
        {
            "number_of_teams": 10,
            "days_between_rounds": 7
        }
    )
    print(">> Creating network")
    s.create_data()
    print(">> Printing network")
    s.print_data()
