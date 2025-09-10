import networkx as nx
import plotly.graph_objects as go
from networkx import MultiDiGraph
import numpy as np
from dfg_rating.model.network.random_network import ConfigurationModelNetwork
from dfg_rating.model.rating.controlled_trend_rating import ControlledTrendRating, ControlledRandomFunction

#%%

n = 100
sequence = n * [10]
directed_conf = nx.directed_configuration_model(4 * [3], 4 * [3])
#%%
print(directed_conf.edges)
print([e for e in nx.selfloop_edges(directed_conf)])
print([d for v, d in directed_conf.degree()])
directed_conf.remove_edges_from(list(nx.selfloop_edges(directed_conf)))
print("directed configuration model")
print([e for e in nx.selfloop_edges(directed_conf)])
print(directed_conf.edges)
print(np.mean([d for v, d in directed_conf.degree()]))

#%%
random_network = ConfigurationModelNetwork(
    teams=n,
    days_between_rounds=3,
    true_rating=ControlledTrendRating(
        starting_point=ControlledRandomFunction(distribution='normal', loc=1000, scale=100),
        delta=ControlledRandomFunction(distribution='normal', loc=0, scale=3),
        trend=ControlledRandomFunction(distribution='normal', loc=0, scale=20/365),
        season_delta=ControlledRandomFunction(distribution='normal', loc=0, scale=10)
    ),
    expected_home_matches=20,
    expected_away_matches=20,
    variance_home_matches=5,
    variance_away_matches=5
)
