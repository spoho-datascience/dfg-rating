import pandas as pd
import networkx as nx
df = pd.read_csv('/home/marc/Development/dshs/dfg-rating/data/real/ATP_Network_2010_2019.csv')

G = nx.DiGraph()

for row_id, row_info in df.iterrows():
    print(row_id, row_info)
