import math
import networkx as nx

from dfg_rating.model.bookmaker.base_bookmaker import BaseBookmaker
from dfg_rating.model.forecast.base_forecast import BaseForecast
from dfg_rating.model.network.base_network import BaseNetwork, base_edge_filter
from dfg_rating.model.rating.base_rating import BaseRating
from dfg_rating.model.rating.function_rating import FunctionRating


class RoundRobinNetwork(BaseNetwork):
    """Class that defines a Network modeling a Round-Robin tournamnet (all-play-all tournament).
    A competition in which each contestant meets all other contestants in turn)

    """
    def __init__(self, **kwargs):
        super().__init__(f"{kwargs.get('extra_type', '')}-round-robin", **kwargs)

    def fill_graph(self, team_labels={}, season=0):
        """Propagates data from parameters.
                Updating self.data as the resulting network of matches scheduled.
                Implementing Berger Tables Scheduling algorithm.

                Returns:
                    boolean: True if the process has been successful, False if else.
                """
        if self.data is None:
            graph = nx.MultiDiGraph()
        else:
            graph = self.data
        number_of_teams = len(list(team_labels.keys()))
        if number_of_teams == 0:
            number_of_teams = self.n_teams
            number_of_rounds = self.n_rounds
        else:
            number_of_rounds = number_of_teams - 1 + number_of_teams % 2

        n_games_per_round = self.params.get('games_per_round', int(math.ceil(number_of_teams / 2)))

        teams_list = [t for t in range(0, number_of_teams)]
        if number_of_teams % 2 != 0:
            teams_list.append(-1)

        slice_a = teams_list[0:n_games_per_round]
        slice_b = teams_list[n_games_per_round:]
        fixed = teams_list[0]

        day = 1
        for season_round in range(0, number_of_rounds):
            for game in range(0, n_games_per_round):
                if (slice_a[game] != -1) and (slice_b[game] != -1):
                    if season_round % 2 == 0:
                        graph.add_edge(
                            team_labels.get(slice_a[game], slice_a[game]),
                            team_labels.get(slice_b[game], slice_b[game]),
                            season=season, round=season_round, day=day
                        )
                        graph.add_edge(
                            team_labels.get(slice_b[game], slice_b[game]),
                            team_labels.get(slice_a[game], slice_a[game]),
                            season=season, round=season_round + number_of_rounds, day=day + (number_of_rounds * self.days_between_rounds)
                        )
                    else:
                        graph.add_edge(
                            team_labels.get(slice_b[game], slice_b[game]),
                            team_labels.get(slice_a[game], slice_a[game]),
                            season=season, round=season_round, day=day
                        )
                        graph.add_edge(
                            team_labels.get(slice_a[game], slice_a[game]),
                            team_labels.get(slice_b[game], slice_b[game]),
                            season=season, round=season_round + number_of_rounds, day=day + (number_of_rounds * self.days_between_rounds)
                        )

            day += self.days_between_rounds
            rotate = slice_a[-1]
            slice_a = [fixed, slice_b[0]] + slice_a[1:-1]
            slice_b = slice_b[1:] + [rotate]

        if self.data is None:
            self.data = graph

    def create_data(self):
        self.data = self.fill_graph()
        return True

    def add_rating(self, rating: BaseRating, rating_name, team_id=None, season=None):
        def edge_filter(e):
            new_filter = (
                (e[3]['season'] == season)
            )
            return new_filter
        if team_id:
            self._add_rating_to_team(team_id, rating.get_ratings(
                self, [team_id], edge_filter if season else base_edge_filter()
            ), rating_name, season=season)
        else:
            ratings = rating.get_all_ratings(self, edge_filter if season else base_edge_filter)
            for team in self.data.nodes:
                self._add_rating_to_team(int(team), ratings[int(team)], rating_name, season=season)

    def add_forecast(self, forecast: BaseForecast, forecast_name):
        for match in self.data.edges:
            self._add_forecast_to_team(match, forecast, forecast_name)

    def add_odds(self, bookmaker_name: str, bookmaker: BaseBookmaker):
        for away_team, home_team, edge_key, edge_attributes in self.iterate_over_games():
            if 'true_forecast' not in edge_attributes['forecasts']:
                print("Playing season: Missing True forecast")
            match_true_forecast = edge_attributes['forecasts']['true_forecast']
            self.data.edges[
                away_team, home_team
            ].setdefault(
                'odds', {}
            )[bookmaker_name] = bookmaker.get_odds(match_true_forecast)
