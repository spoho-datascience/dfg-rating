import json

from dfg_rating.db.postgres import PostgreSQLDriver
from dfg_rating.model import factory
from dfg_rating.model.network.base_network import BaseNetwork

test_network: BaseNetwork = factory.new_network('round-robin', teams=20, days_between_rounds=3)
test_network.create_data()
test_network.play()
#test_network.print_data(attributes=True, ratings=True)

serialized_network = test_network.serialize_network('test_network')
p = PostgreSQLDriver()
for table, table_rows in serialized_network.items():
    columns = table_rows[0].keys()
    query_string = f"INSERT INTO {table}({','.join(columns)}) VALUES %s ON CONFLICT DO NOTHING"
    values = [[value for value in r.values()] for r in table_rows]
    p.insert_many(query_string, values)
p.close()


