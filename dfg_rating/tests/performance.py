from dfg_rating.model.network.simple_network import RoundRobinNetwork
import time
from tqdm import tqdm


import dash_cytoscape as cyto

import dfg_rating.viz.jupyter_widgets as DFGWidgets

from dfg_rating.model.rating.controlled_trend_rating import ControlledTrendRating, ControlledRandomFunction
from dfg_rating.model.rating.elo_rating import ELORating

start_time = time.time()
r = RoundRobinNetwork(
    teams=20,
    days_between_rounds=3
)
print(f"Creating time {time.time() - start_time} seconds")
new_rating = ControlledTrendRating(
    starting_point=ControlledRandomFunction(distribution='normal', loc=1000, scale=150),
    delta=ControlledRandomFunction(distribution='normal', loc=0, scale=2),
    trend=ControlledRandomFunction(distribution='normal', loc=0, scale=.2),
    season_delta=ControlledRandomFunction(distribution='normal', loc=0, scale=10)
)

tested_rating = ELORating(trained=True)

for i in range(1):
    pre_loop_time = time.time()
    winners = []
    #r.add_rating(new_rating, 'new_rating', season=0)
    r.add_rating(tested_rating, 'elo_rating', season=0)
    print(f"Added rating in {time.time() - pre_loop_time} seconds.")

"""
for i in range(10):
    post_loop_time = time.time()
    for edge in tqdm(r.data.edges(keys=True, data=True)):
        edge[3]["new_data"] = 3
        winner = edge[3]["winner"]

    print(f"Potential performance in {time.time() - post_loop_time}")"""

"""ratings = r.data.nodes[0]
print(ratings)"""

"""cyto.load_extra_layouts()
ratings_app = DFGWidgets.RatingsExplorer(network=r, offline=True)
print("running app")
ratings_app.run('external', debug=True, port=8001)"""
