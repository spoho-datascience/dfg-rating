"""Module of helpers for Network visualizations
"""
import datetime
import networkx as nx
import plotly.graph_objects as go
from networkx import degree

from dfg_rating.model.network.base_network import BaseNetwork, base_edge_filter


def create_network_figure(network: BaseNetwork, filter_edge=base_edge_filter) -> go.Figure:
    """Network visualization

    Creates a figure positioning all the nodes and edges of a given network.
    See https://networkx.org/documentation/stable/reference/drawing.html#module-networkx.drawing.layout for graph
    viz options.

    Args:
        network: Sport network of teams and matches.
        filter_edge: Optional; Function to filter the edges of the network.

    Returns:
        A dict-based plotly Figure object with network visualization.

    """
    # Assigning node positions
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


def network_to_cyto(network: BaseNetwork):
    elements = []
    """list_of_degrees = sorted(degree(network.data), key=lambda t: t[1])
    print([(player_id, network.data.nodes[player_id]['name'], connection) for player_id, connection in list_of_degrees[-10:]])
    top_connected_players_ids = [player_id for player_id, connection in list_of_degrees[-10:]]
    """
    for node1, node2, edge_key, edge_info in network.iterate_over_games():
        # if node1 in top_connected_players_ids or node2 in top_connected_players_ids:
        if edge_info['round'] > 2:
            break
        elements += [
            {
                "data": {
                    "id": node1,
                    "label": f"R{node1}: {network.data.nodes[node1].get('ratings', {}).get('true_rating', {}).get(0, [])[0]:.2f}",
                }
            },
            {
                "data": {
                    "id": node2,
                    "label": f"R{node2}: {network.data.nodes[node2].get('ratings', {}).get('true_rating', {}).get(0, [])[0]:.2f}",
                }
            },
        ]
        elements += [
                {
                    "data": {
                        "id": f"{node2}_{node1}_{edge_info['season']}",
                        "source": node2, "target": node1,
                        "label": f"{edge_info['forecasts']['true_forecast'].print()}"
                    },
                    "classes": f"{edge_info['winner']}"
                }
        ]
        break
    return elements


def network_to_cyto_serialized():
    return []


cyto_stylesheet = [
    {
        'selector': 'node',
        'style': {
            'label': 'data(label)'
        }
    },
    {
        'selector': 'edge',
        'style': {
            'label': 'data(label)',
            'curve-style': 'bezier',
            'source-arrow-shape': 'triangle',
            'line-color': 'lightgray'
        }
    },
    {
        'selector': '.home',
        'style': {
            'line-color': 'green'
        }
    },
    {
        'selector': '.away',
        'style': {
            'line-color': 'yellow'
        }
    },
    {
        'selector': '.draw',
        'style': {
            'line-color': 'lightblue'
        }
    }

]
