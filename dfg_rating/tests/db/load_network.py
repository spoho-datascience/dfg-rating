from typing import Dict

from dfg_rating.db.postgres import PostgreSQLDriver
from dfg_rating.logic.controller import Controller
from dfg_rating.model import factory
from dfg_rating.model.network.base_network import WhiteNetwork, BaseNetwork

mc = Controller()

mc.load_network_from_sql("test_network")

all_matches = [(a,h,m_id,attributes) for a,h,m_id,attributes in mc.networks["test_network"].iterate_over_games() if a == '0']

print(all_matches[:100])
