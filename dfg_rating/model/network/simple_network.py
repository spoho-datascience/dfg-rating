import math
import networkx as nx

from dfg_rating.model.bookmaker.base_bookmaker import BaseBookmaker
from dfg_rating.model.forecast.base_forecast import BaseForecast
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
                        graph.add_edge(slice_b[game], slice_a[game], round=season_round + self.n_rounds,
                                       day=day + (self.n_rounds * self.days_between_rounds))
                    else:
                        graph.add_edge(slice_b[game], slice_a[game], round=season_round, day=day)
                        graph.add_edge(slice_a[game], slice_b[game], round=season_round + self.n_rounds,
                                       day=day + (self.n_rounds * self.days_between_rounds))

            day += self.days_between_rounds
            rotate = slice_a[-1]
            slice_a = [fixed, slice_b[0]] + slice_a[1:-1]
            slice_b = slice_b[1:] + [rotate]

        self.data = graph
        return True

    def add_rating(self, rating: BaseRating, rating_name, team_id=None):
        if team_id:
            self._add_rating_to_team(team_id, rating.get_ratings(self, [team_id]), rating_name)
        else:
            ratings = rating.get_all_ratings(self)
            for team in self.data.nodes:
                self._add_rating_to_team(int(team), ratings[int(team)], rating_name)

    def add_forecast(self, forecast: BaseForecast, forecast_name):
        for match in self.data.edges:
            self._add_forecast_to_team(match, forecast, forecast_name)

    def add_odds(self, bookmaker_name: str, bookmaker: BaseBookmaker):
        for away_team, home_team, edge_attributes in self.iterate_over_games():
            if 'true_forecast' not in edge_attributes['forecasts']:
                print("Playing season: Missing True forecast")
            match_true_forecast = edge_attributes['forecasts']['true_forecast']
            self.data.edges[
                away_team, home_team
            ].setdefault(
                'odds', {}
            )[bookmaker_name] = bookmaker.get_odds(match_true_forecast)
