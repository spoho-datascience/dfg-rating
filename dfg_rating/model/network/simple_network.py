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

    def print_data(self, **print_kwargs):
        if print_kwargs.get('schedule', False):
            print("Network schedule")
            for away_team, home_team, edge_attributes in sorted(self.data.edges.data(), key=lambda t: t[2]['round']):
                print(f"({away_team} -> {home_team} at round {edge_attributes['round']}, day {edge_attributes['day']})")
                if (print_kwargs.get('winner', False)) & ('winner' in edge_attributes):
                    print(f"Result: {edge_attributes['winner']}")
                if (print_kwargs.get('forecasts', False)) & ('forecasts' in edge_attributes):
                    forecasts_list = print_kwargs.get('forecasts_list', [])
                    if len(forecasts_list) == 0:
                        forecasts_list = list(edge_attributes['forecasts'].keys())
                    for forecast in forecasts_list:
                        print(f"Forecast {forecast}: {edge_attributes['forecasts'][forecast].print()}")
                if (print_kwargs.get('odds', False)) & ('odds' in edge_attributes):
                    bookmakers_list = print_kwargs.get('bookmakers_list', [])
                    if len(bookmakers_list) == 0:
                        bookmakers_list = list(edge_attributes['odds'].keys())
                    for bm in bookmakers_list:
                        print(f"Bookmaker {bm} odds: {edge_attributes['odds'][bm]}")
            print("---------------")
        if print_kwargs.get('attributes', False):
            if (print_kwargs.get('ratings', False)) & ('ratings' in self.data.nodes[0]):
                print("Teams ratings")
                for team in self.data.nodes:
                    print(f"Team {team}:")
                    ratings_list = print_kwargs.get('ratings_list', [])
                    if len(ratings_list) == 0:
                        ratings_list = list(self.data.nodes[team]['ratings'].keys())
                    for rating in ratings_list:
                        print(f"Rating {rating} for team {team}: > {self.data.nodes[team]['ratings'][rating]}")

    def iterate_over_games(self):
        return sorted(self.data.edges.data(), key=lambda t: t[2]['round'])

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
