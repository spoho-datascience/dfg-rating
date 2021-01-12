from typing import Dict

from dfg_rating.db.postgres import PostgreSQLDriver
from dfg_rating.model import factory
from dfg_rating.model.network.base_network import WhiteNetwork, BaseNetwork

p = PostgreSQLDriver()
p.connect()
network_name = "test_network"

networks = p.execute_query(query=f"SELECT * FROM public.networks m WHERE m.network_name = '{network_name}'")
print(networks)
matches = p.execute_query(query=f"SELECT * FROM public.matches m WHERE m.network_name = '{network_name}'")
print(matches)
forecasts = p.execute_query(query=f"SELECT * FROM public.forecasts f WHERE f.network_name = '{network_name}'")
#print(forecasts)
ratings = p.execute_query(query=f"SELECT * FROM public.ratings r WHERE r.network_name = '{network_name}'")
#print(ratings)
matches_with_forecasts = p.execute_query()

networks_dict: Dict[str, BaseNetwork] = {}
for network in networks:
    networks_dict.setdefault(
        network['network_name'],
        factory.new_network(network['network_type'])
    ).deserialize_network(
        matches=matches,
        forecasts=forecasts,
        ratings=ratings
    )

for n_name, n in networks_dict.items():
    n.print_data(schedule=True, forecasts=True)