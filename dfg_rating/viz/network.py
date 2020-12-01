import networkx as nx
import plotly.graph_objects as go

from dfg_rating.model.network.base_network import BaseNetwork, base_edge_filter


def create_network_figure(network: BaseNetwork, filter_edge=base_edge_filter):
    # Code for viz network
    # Assigning node positions
    network.print_data(schedule=True)
    graph = nx.MultiDiGraph(((u, v, k, e) for u, v, k, e in network.data.edges.data(keys=True, data=True)))
    pos = nx.kamada_kawai_layout(graph)
    for n, p in pos.items():
        graph.nodes[n]['pos'] = p

    edge_traces = []

    for season in range(5):
        # Edge traces
        edge_x = []
        edge_y = []

        for edge in graph.edges(data=True):
            if edge[2]['season'] == season:
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
            line=dict(width=0.5, color='lightgray'),
            hoverinfo='none',
            mode='lines',
            name=f"Season {season}"
        )
        edge_traces.append(edge_trace)

    # Node traces
    node_x = []
    node_y = []
    node_names = []
    for node in graph.nodes():
        x, y = graph.nodes[node]['pos']
        node_x.append(x)
        node_y.append(y)
        node_names.append(node)

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        text=node_names,
        textposition="bottom center",
        name="Teams",
        marker=dict(
            size=10,
            line_width=2))

    fig = go.Figure(data=edge_traces + [node_trace],
                    layout=go.Layout(
                        title='Network graph',
                        titlefont_size=16,
                        showlegend=True,
                        hovermode='closest',
                        margin=dict(b=20, l=5, r=5, t=40),
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                    )
    return fig