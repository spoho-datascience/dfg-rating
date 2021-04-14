import pandas as pd
import os

from dfg_rating.logic import controller

print(os.path.abspath(os.path.curdir))

mc = controller.Controller()
mc.load_network_from_tabular(
    network_name='soccer_national',
    file_path='../../data/real/nation_teams_competitions.xlsx',
    new_mapping='soccer'
)
mc.load_network_from_tabular(
    network_name='tennis_full',
    file_path='../../data/real/ATP_Network_2010_2019.csv',
    new_mapping='atp'
)
mc.save_network('soccer_national')
mc.save_network('tennis_full')


