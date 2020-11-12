import pandas as pd
import networkx as nx

from dfg_rating.model.network.base_network import WhiteNetwork

df = pd.read_csv('/home/marc/Development/dshs/dfg-rating/data/real/ATP_Network_2010_2019.csv')

white_network = WhiteNetwork(data=df)
white_network.create_data()
white_network.print_data(attributes=True)
