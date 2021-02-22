"""Module of helpers for Network visualizations
"""
import datetime
import networkx as nx
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from networkx import degree

from dfg_rating.model.network.base_network import BaseNetwork, base_edge_filter

country_names = {
    "Luxemburg": "Luxembourg",
    "Nordmazedonien": "Macedonia",
    "Slowakei": "Slovakia",
    "Belarus": "Belarus",
    "Ukraine": "Ukraine",
    "Spanien": "Spain",
    "Slowenien": "Slovenia",
    "England": "England",
    "Schweiz": "Switzerland",
    "Estland": "Estonia",
    "San Marino": "San Marino",
    "Litauen": "Lithuania",
    "Nordirland": "Northern Ireland",
    "Rumänien": "Romania",
    "Griechenland": "Greece",
    "Ungarn": "Hungary",
    "Finnland": "Finland",
    "Färöer": "Faroe Islands",
    "Norwegen": "Luxemburg",
    "Italien": "Italy",
    "Kroatien": "Croatia",
    "Malta": "Malta",
    "Aserbaidschan": "Azerbaijan",
    "Bulgarien": "Bulgaria",
    "Polen": "Poland",
    "Gibraltar": "Gibraltar",
    "Irland": "Republic of Ireland",
    "Schottland": "Scotland",
    "Deutschland": "Germany",
    "Georgien": "Georgia",
    "Wales": "Wales",
    "Belgien": "Belgium",
    "Israel": "Israel",
    "Zypern": "Cyprus",
    "Andorra": "Andorra",
    "Bosnien-Herzegowina": "Bosnia and Herzegovina",
    "Dänemark": "Denmark",
    "Armenien": "Armenia",
    "Serbien": "Serbia",
    "Portugal": "Portugal",
    "Albanien": "Albania",
    "Montenegro": "Montenegro",
    "Schweden": "Sweden",
    "Russland": "Russia",
    "Moldau": "Moldova",
    "Österreich": "Austria",
    "Liechtenstein": "Liechtenstein",
    "Türkei": "Turkey",
    "Niederlande": "Netherlands",
    "Lettland": "Latvia",
    "Kasachstan": "Kazakhstan",
    "Island": "Iceland",
    "Tschechien": "Czech Republic",
    "Frankreich": "France"
}

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
    list_of_degrees = sorted(degree(network.data), key=lambda t: t[1])
    #print([(player_id, network.data.nodes[player_id]['name'], connection) for player_id, connection in list_of_degrees[-10:]])
    top_connected_players_ids = [player_id for player_id, connection in list_of_degrees[-50:]]
    top_30_dict = {
        '283': 'Haase R.',
        '402': 'Lajovic D.',
        '190': 'Dzumhur D.',
        '221': 'Fritz',
        '324': 'Jaziri',
        '675': 'Sousa J.',
        '445': 'Mannarino A.',
        '361': 'Klizan M.',
        '117': 'Chardy J.',
        '191': 'Ebden M.',
        '701': 'Tiafoe F.',
        '322': 'Jarry N.',
        '222': 'Fucsovics M.',
        '398': 'Kyrgios N.',
        '366': 'Kohlschreiber P.',
        '641': 'Seppi A.',
        '328': 'Johnson S.',
        '479': 'Millman J.',
        '565': 'Pouille L.',
        '152': 'De Minaur A.',
        '657': 'Simon G.',
        '490': 'Monfils G.',
        '738': 'Verdasco F.',
        '648': 'Shapovalov D.',
        '234': 'Gasquet R.',
        '122': 'Chung H.',
        '54': 'Bautista Agut R.',
        '107': 'Carreno Busta P.',
        '250': 'Goffin D.',
        '52': 'Basilashvili N.',
        '111': 'Cecchinato, M.',
        '173': 'Dimitrov G.',
        '582': 'Raonic M.',
        '638': 'Schwartzamn',
        '466': 'Medvedev, D.',
        '715': 'Tsitsipas S.',
        '192': 'Edmund, K.',
        '218': 'Fognini F.',
        '133': 'Coric, B.',
        '345': 'Khachanov, K.',
        '316': 'Isner J.',
        '524': 'Nishikori K.',
        '698': 'Thiem D.',
        '124': 'Cilic M.',
        '17': 'Anderson K.',
        '781': 'Zverev A.',
        '160': 'Del Potro J.M.',
        '211': 'Federer R.',
        '508': 'Nadal R.',
        '176': 'Djokovic N.'
    }
    top_30_ids = list(top_30_dict.keys())[-15:]
    print(top_30_ids)
    random_players = np.random.choice([player_id for player_id, conn in list_of_degrees], 200)
    #print(random_players)
    for node1, node2, edge_key, edge_info in network.iterate_over_games():
        # if node1 in top_connected_players_ids or node2 in top_connected_players_ids:
        if (
                edge_info['Tournament'] in ['EM', 'EM Quali']
        ) and (
                str(edge_info['Season ']) in ['2016', '2014/2015']
        ):
            print(node1, node2, edge_key, edge_info)
            elements += [
                {
                    "data": {
                        "id": node1,
                        "label": f"{country_names[node1]}",
                    },
                },
                {
                    "data": {
                        "id": node2,
                        "label": f"{country_names[node2]}",
                    },
                },
            ]
            elements += [
                    {
                        "data": {
                            "id": f"{node2}_{node1}_{edge_info['season']}",
                            "source": node2, "target": node1
                        },
                        "classes": f"{str(edge_info['Season '])[-1]}_{edge_info['Round']}"
                    }
            ]
        """elements += [
            {
                "data": {
                    "id": node1,
                    "label": f"Team {node1}",
                }
            },
            {
                "data": {
                    "id": node2,
                    "label": f"Team {node2}",
                }
            },
        ]
        elements += [
            {
                "data": {
                    "id": f"{node2}_{node1}_{edge_info['season']}",
                    "source": node2, "target": node1
                }
            }
        ]"""
        """if (edge_info['Date'].date() > datetime.date(2019, 1, 1)) and ((
                edge_info['WRank'] <= 20) and (
                edge_info['LRank'] <= 20)):"""
        """if (edge_info['Date'].date() > datetime.date(2019, 1, 1)) and (str(node1) in top_30_ids) and (str(node2) in top_30_ids):
            elements += [
                {
                    "data": {
                        "id": node1,
                        "label": f"{network.data.nodes[node1]['name']}",
                    },
                    "classes": "top" if node1 in top_connected_players_ids else "-"
                },
                {
                    "data": {
                        "id": node2,
                        "label": f"{network.data.nodes[node2]['name']}",
                    },
                    "classes": "top" if node2 in top_connected_players_ids else "-"
                },
            ]
            elements += [
                {
                    "data": {
                        "id": f"{node2}_{node1}_{edge_info['Tournament']}_{str(edge_info['Date'])}",
                        "source": node2, "target": node1
                    }
                }
            ]"""

    return elements


def custom_cyto_network():
    elements = []
    for i in range(5):
        elements.append(
            {
                "data": {
                    "id": i+1,
                    "label": f"actor {i+1}",
                },
            },
        )
    elements += [
        {
            "data": {
                "id": "first", "label": "Round 1. Winner: Actor 1",
                "source": "1", "target": "3"
            }
        },
        {
            "data": {
                "id": "second", "label": "Round 1. Winner: Actor 5",
                "source": "2", "target": "5"
            }
        },
        {
            "data": {
                "id": "third", "label": "Round 2. Winner: Actor 5",
                "source": "5", "target": "4"
            }
        },
    ]
    return elements


def network_to_cyto_serialized():
    return []


cyto_stylesheet = [
    {
        'selector': 'node',
        'style': {
            'label': 'data(label)',
            'background-color': "gray"
        }
    },
    {
        'selector': 'edge',
        'style': {
            'label': 'data(label)',
            'curve-style': 'bezier',
            'target-arrow-shape': 'triangle',
            'target-arrow-color': 'gray',
            'line-color': 'lightgray'
        }
    },
    {
        'selector': '.not_qualified',
        'style': {
            'background-color': 'lightgray'
        }
    },
    {
        'selector': '.5_Playoffs',
        'style': {
            'line-color': 'lightgray',
            'line-style': 'dashed',

        }
    },
    {
        'selector': '.6_Gruppenphase',
        'style': {
            'line-color': 'gray',
            'line-style': 'dashed'
        }
    },
    {
        'selector': '.6_Achtelfinale',
        'style': {
            'line-color': 'gray'
        }
    },
    {
        'selector': '.6_Viertelfinale',
        'style': {
            'line-color': 'gray'
        }
    },
    {
        'selector': '.6_Halbfinale',
        'style': {
            'line-color': 'gray'
        }
    },
    {
        'selector': '.6_Finale',
        'style': {
            'line-color': 'black'
        }
    }

]
