from datetime import date
import numpy as np
import networkx as nx
import pandas as pd
from abc import ABC, abstractmethod
from typing import NewType

from dfg_rating.model.bookmaker.base_bookmaker import BaseBookmaker
from dfg_rating.model.forecast.base_forecast import BaseForecast
from dfg_rating.utils.command_line import show_progress_bar

TeamId = NewType('TeamId', int)


def weighted_winner(forecast: BaseForecast):
    weights = forecast.get_forecast().cumsum()
    x = np.random.default_rng().uniform(0, 1)
    for i in range(len(weights)):
        if x < weights[i]:
            return forecast.outcomes[i]


class BaseNetwork(ABC):
    """Abstract class defining the interface of Network object.
    A network is a set of nodes and edges defining the relationship between teams in a tournament.
    Teams can be modelled as individuals (Tennis) or collective teams (soccer).
    An edge between two teams identifies a competition between them

    Attributes:
        network_type (str): Text descriptor of the network type.
        kwargs (dict): Dictionary of key-value parameters for the network configuration

    """

    def __init__(self, network_type: str, **kwargs):
        self.data = None
        self.type = network_type
        self.params = kwargs
        self.n_teams = self.params.get('number_of_teams', 0)
        self.n_rounds = self.params.get('rounds', self.n_teams - 1 + self.n_teams % 2)
        self.days_between_rounds = self.params.get('days_between_rounds', 1)

    @abstractmethod
    def create_data(self):
        """Creates network data including teams and matches
        """
        pass

    @abstractmethod
    def print_data(self, **kwargs):
        """Serialize and print via terminal the network content.
        """
        pass

    @abstractmethod
    def iterate_over_games(self):
        pass

    def play(self):
        for away_team, home_team, edge_attributes in self.iterate_over_games():
            # TODO construct an object Match
            # Random winner with weighted choices
            if 'true_forecast' not in edge_attributes['forecasts']:
                print("Playing season: Missing True forecast")
            winner = weighted_winner(edge_attributes['forecasts']['true_forecast'])
            self.data.edges[away_team, home_team]['winner'] = winner

    def _add_rating_to_team(self, team_id, rating_values, rating_name):
        self.data.nodes[team_id].setdefault('ratings', {})[rating_name] = rating_values

    def _add_forecast_to_team(self, match, forecast: BaseForecast, forecast_name):
        self.data.edges[match].setdefault('forecasts', {})[forecast_name] = forecast

    @abstractmethod
    def add_rating(self, new_rating, rating_name):
        pass

    @abstractmethod
    def add_forecast(self, forecast: BaseForecast, forecast_name):
        pass

    @abstractmethod
    def add_odds(self, bookmaker_name: str, bookmaker: BaseBookmaker):
        pass


class WhiteNetwork(BaseNetwork):
    """Fully flexible network to be created out of a table structure"""

    def __init__(self, **kwargs):
        super().__init__("white", **kwargs)
        self.table_data: pd.DataFrame = kwargs['data']
        self.table_data['Date'] = pd.to_datetime(self.table_data.Date)
        self.table_data.sort_values(by="Date", inplace=True)

    def create_data(self):
        graph = nx.DiGraph()
        sp = show_progress_bar(text="Loading network", start=True)
        day = 0
        for row_id, row in self.table_data.iterrows():
            if day == 0:
                day = 1
                first_date = row['Date']
            delta = row['Date'] - first_date
            day += delta.days
            # Add edge (create if needed the nodes and attributes)
            edge_dict = {key: value for key, value in row.items() if key not in ['WinnerID', 'LoserID']}
            edge_dict['day'] = day
            graph.add_edge(row['WinnerID'], row['LoserID'], **edge_dict)
            graph.nodes[row['WinnerID']]['name'] = row['Winner']
            graph.nodes[row['LoserID']]['name'] = row['Loser']
        show_progress_bar("Network Loaded", False, sp)
        self.data = graph
        return True

    def print_data(self, **print_kwargs):
        if print_kwargs.get('schedule', False):
            print("Network schedule")
            for away_team, home_team, edge_attributes in sorted(self.data.edges.data(), key=lambda t: t[2]['day']):
                print(f"({home_team} vs. {away_team} at ATP {edge_attributes['ATP']}, day {edge_attributes['day']})")

            print("---------------")
        if print_kwargs.get('attributes', False):
            for node in self.data.nodes:
                print(f"Node id: {node}, Name: {self.data.nodes[node]['name']}")

    def iterate_over_games(self):
        pass

    def add_rating(self, new_rating, rating_name):
        pass

    def add_forecast(self, forecast: BaseForecast, forecast_name):
        pass

    def add_odds(self, bookmaker_name: str, bookmaker: BaseBookmaker):
        pass