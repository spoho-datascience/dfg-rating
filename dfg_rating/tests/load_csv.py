import plotly.graph_objects as go
import pandas as pd
import networkx as nx
from datetime import date

from dfg_rating.model.network.base_network import WhiteNetwork

df = pd.read_csv('/home/marc/Development/dshs/dfg-rating/data/real/ATP_Network_2010_2019.csv')

# %%
white_network = WhiteNetwork(data=df)
white_network.create_data()
# %%

white_network.print_data(attributes=True)


# %%
def filter_edge(e):
    filter = (
            (e['Date'] < date(year=2011, month=2, day=1))
    )
    return True


# Code for viz network
# Assigning node positions
graph = nx.Graph(((u, v, e) for u, v, e in white_network.data.edges.data() if filter_edge(e)))
pos = nx.kamada_kawai_layout(graph)
for n, p in pos.items():
    graph.nodes[n]['pos'] = p

# Edge traces
edge_x = []
edge_y = []

for edge in graph.edges():
    x0, y0 = graph.nodes[edge[0]]['pos']
    x1, y1 = graph.nodes[edge[1]]['pos']
    edge_x.append(x0)
    edge_x.append(x1)
    edge_x.append(None)
    edge_y.append(y0)
    edge_y.append(y1)
    edge_y.append(None)

edge_trace = go.Scatter(
    x=edge_x, y=edge_y,
    line=dict(width=0.5, color='#888'),
    hoverinfo='none',
    mode='lines')

# Node traces
node_x = []
node_y = []
node_names = []
for node in graph.nodes():
    x, y = graph.nodes[node]['pos']
    node_x.append(x)
    node_y.append(y)
    node_names.append(white_network.data.nodes[node]["name"])

node_trace = go.Scatter(
    x=node_x, y=node_y,
    mode='markers',
    hovertext=node_names,
    hoverinfo='text',
    marker=dict(
        showscale=True,
        # colorscale options
        # 'Greys' | 'YlGnBu' | 'Greens' | 'YlOrRd' | 'Bluered' | 'RdBu' |
        # 'Reds' | 'Blues' | 'Picnic' | 'Rainbow' | 'Portland' | 'Jet' |
        # 'Hot' | 'Blackbody' | 'Earth' | 'Electric' | 'Viridis' |
        colorscale='YlGnBu',
        reversescale=True,
        color=[],
        size=10,
        colorbar=dict(
            thickness=15,
            title='Node Connections',
            xanchor='left',
            titleside='right'
        ),
        line_width=2))

node_adjacencies = []
node_text = []
for node, adjacencies in enumerate(graph.adjacency()):
    node_adjacencies.append(len(adjacencies[1]))
    node_text.append('# of connections: ' + str(len(adjacencies[1])))

node_trace.marker.color = node_adjacencies
node_trace.text = node_text

fig = go.Figure(data=[edge_trace, node_trace],
                layout=go.Layout(
                    title='<br>Network graph',
                    titlefont_size=16,
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=20, l=5, r=5, t=40),
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                )
fig.show()
