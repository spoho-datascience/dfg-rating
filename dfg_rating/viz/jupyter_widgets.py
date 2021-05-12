import numpy as np
import plotly.express as px
from dash.exceptions import PreventUpdate
from jupyter_dash import JupyterDash
import dash_core_components as dcc
import dash_cytoscape as cyto
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash.dependencies as Callback

import pandas as pd

from dfg_rating.model.network.base_network import BaseNetwork
from dfg_rating.viz import tables
from dfg_rating.viz.charts import create_ratings_charts, publication_chart


class BaseWidget:
    def __init__(self, app_name=__name__, **kwargs):
        self.app = JupyterDash(app_name, external_stylesheets=[dbc.themes.SANDSTONE], **kwargs)
        self.build_layout()
        self.configure_callbacks()

    def run(self, mode='inline', **kwargs):
        self.app.run_server(mode=mode, **kwargs)

    def build_layout(self):
        self.app.layout = html.Div(
            html.H1("DFG Rating widgets library for Jupyter Notebooks")
        )

    def configure_callbacks(self):
        pass


class NetworkExplorer(BaseWidget):

    def __init__(self, network: BaseNetwork, **kwargs):
        self.network = network
        self.extra_node_properties = kwargs.pop('node_props', [])
        self.extra_edge_properties = kwargs.pop('edge_props', [])
        super().__init__(app_name="network_explorer", **kwargs)

    def build_layout(self):
        cyto_stylesheet = [
            {
                'selector': 'node',
                'style': {
                    'label': 'data(label)',
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
            }
        ]
        cyto_elements, analysis_dict = self.network_to_cyto()
        self.app.layout = dbc.Container(
            [
                dbc.Row(
                    dbc.Col(html.H1("Network explorer"), align="center", width=6),
                    justify='center'
                ),
                dbc.Row(
                    children=[
                        dbc.Col(
                            children=[
                                         html.H4("Data Filter"),
                                     ] + self.data_filter_layout() + [
                                html.Hr(),
                                html.H4("Network settings"),
                                html.P("Drawing options:"),
                                dcc.Dropdown(
                                    id="dropdown-layout",
                                    options=[
                                         {
                                             "label": layout_option,
                                             "value": layout_option
                                         } for layout_option in
                                         [
                                             'random',
                                             'grid',
                                             'circle',
                                             'concentric',
                                             'breadthfirst',
                                             'cose',
                                             'cose-bilkent',
                                             'dagre',
                                             'cola',
                                             'klay',
                                             'spread',
                                             'euler'
                                         ]
                                     ],
                                    value="grid",
                                ),
                                html.Br(),
                                dbc.Button(
                                    id="btn-download",
                                    children="Download network as PNG"
                                ),
                                html.Br(),
                                html.Div(tables.calendar_table(pd.DataFrame(analysis_dict)))
                             ],
                            width=4
                        ),
                        dbc.Col(
                            children=dbc.Spinner(cyto.Cytoscape(
                                id="network_cyto",
                                elements=cyto_elements,
                                stylesheet=cyto_stylesheet,
                                style={
                                    "height": "95vh",
                                    'width': '100%'
                                }
                            )),
                            width=8
                        )
                    ]
                )
            ], fluid=True
        )

    def configure_callbacks(self):
        @self.app.callback([Callback.Output('network_cyto', 'layout'),
                            Callback.Output('network_cyto', 'elements'),
                            Callback.Output('kalender-table', 'data')],
                           [Callback.Input('dropdown-layout', 'value'),
                            Callback.Input("nodes_options_id", "value"),
                            Callback.Input("edges_options_season", "value"),
                            Callback.Input({'type': 'nodes_filter', 'index': Callback.ALL}, 'value'),
                            Callback.Input({'type': 'edges_filter', 'index': Callback.ALL}, 'value')])
        def update_cytoscape_layout(layout, id_filter, season_filter, nodes_filter, edges_filter):
            filter_nodes = {}
            filter_edges = {}
            if (id_filter is not None) and (len(id_filter) > 0):
                filter_nodes["id"] = id_filter
            if season_filter is not None:
                filter_edges["season"] = season_filter
            for i, n_filter in enumerate(nodes_filter):
                if n_filter is not None:
                    filter_nodes[self.extra_node_properties[i]] = n_filter
            for i, e_filter in enumerate(edges_filter):
                if e_filter is not None:
                    filter_edges[self.extra_edge_properties[i]] = e_filter

            cyto_elements, calendar_info = self.network_to_cyto(filter_nodes, filter_edges)
            return {'name': layout}, cyto_elements, pd.DataFrame(calendar_info).to_dict('records')

        @self.app.callback(
            Callback.Output("network_cyto", "generateImage"),
            [
                Callback.Input("btn-download", "n_clicks")
            ])
        def get_image(btn_clicks):
            # File type to ouput of 'svg, 'png', 'jpg', or 'jpeg' (alias of 'jpg')
            ftype = 'svg'
            # 'store': Stores the image data in 'imageData' !only jpg/png are supported
            # 'download'`: Downloads the image as a file with all data handling
            # 'both'`: Stores image data and downloads image as file.
            action = 'download'
            if btn_clicks is None:
                raise PreventUpdate

            return {
                'type': ftype,
                'action': action
            }

    def network_to_cyto(self, nodes_filter={}, edges_filter={}):
        elements = []
        list_of_ids = nodes_filter.get('id', [n for n in self.network.data.nodes()])
        analysis_dict = []
        for node1, node2, edge_key, edge_info in self.network.iterate_over_games():
            if all(node not in list_of_ids for node in [node1, node2]):
                continue
            next_match = False
            for k, v in nodes_filter.items():
                if (k not in ['id']) and (len(v) > 0):
                    node1_value = self.network.data.nodes[node1].get(k, None)
                    node2_value = self.network.data.nodes[node2].get(k, None)
                    next_match = (any(
                        (value is None) or (value not in v) for value in [node1_value, node2_value]
                    )) or next_match
            if next_match:
                continue
            for k, v in edges_filter.items():
                if len(v) > 0:
                    edge_value = edge_info.get(k, None)
                    next_match = ((edge_value is None) or (edge_value not in v)) or next_match
            if next_match:
                continue
            elements += [
                {
                    "data": {
                        "id": node1,
                        "label": f"{self.network.data.nodes[node1].get('name', node1)}",
                    },
                },
                {
                    "data": {
                        "id": node2,
                        "label": f"{self.network.data.nodes[node1].get('name', node2)}",
                    },
                },
            ]
            elements += [
                {
                    "data": {
                        "id": f"{node2}_{node1}_{edge_info['season']}_{edge_info['round']}",
                        "source": node2, "target": node1
                    },
                    "classes": f"Season {(edge_info['season'])}, Round {edge_info['round']}"
                }
            ]
            analysis_dict.append({
                "HomeTeam": self.network.data.nodes[node2].get("name", node2),
                "AwayTeam": self.network.data.nodes[node1].get("name", node1),
                "Season": edge_info.get('season', None),
                "Round": edge_info.get('round', None),
                "Result": edge_info.get('winner', None),
            })
        return elements, analysis_dict

    def data_filter_layout(self):
        data_layout = []
        extra_node_properties = []
        seasons = set([data['season'] for a, h, k, data in self.network.iterate_over_games()])
        for n_prop in self.extra_node_properties:
            if n_prop in self.network.data.nodes()[1].keys():
                extra_node_properties.append(dbc.Row([
                    dbc.Col(html.P(f"{n_prop}: "), width=2),
                    dbc.Col(
                        dcc.Dropdown(
                            id={
                                'type': 'nodes_filter',
                                'index': n_prop,
                            },
                            options=[
                                {
                                    "label": self.network.data.nodes[v].get(n_prop, v), "value": v
                                } for v in sorted(self.network.data.nodes())
                            ],
                            multi=True
                        ),
                    )
                ]))
        extra_edge_properties = []
        for e_prop in self.extra_edge_properties:
            network_projection = self.network.data.edges.data(e_prop)
            options = []
            for node1, node2, prop_value in network_projection:
                if prop_value not in options:
                    options.append(prop_value)
            extra_edge_properties.append(dbc.Row(children=[
                dbc.Col(html.P(f"{e_prop}: "), width=2),
                dbc.Col(
                    dcc.Dropdown(
                        id={
                            'type': 'edges_filter',
                            'index': e_prop,
                        },
                        options=[
                            {
                                "label": o, "value": o
                            } for o in sorted(options)
                        ],
                        multi=True
                    ),
                )
            ]))

        data_layout += [
                           html.H5("Nodes"),
                           dbc.Row(
                               id="nodes_id_row",
                               children=[
                                   dbc.Col(html.P("Team id: "), width=2),
                                   dbc.Col(
                                       dcc.Dropdown(
                                           id=f"nodes_options_id",
                                           options=[
                                               {
                                                   "label": f"Team {v}", "value": v
                                               } for v in sorted(self.network.data.nodes())
                                           ],
                                           multi=True
                                       ),
                                   )
                               ]
                           )
                       ] + extra_node_properties + [
                           html.H5("Edges"),
                           dbc.Row(
                               id="season_row",
                               children=[
                                   dbc.Col(html.P("Season: "), width=2),
                                   dbc.Col(
                                       dcc.Dropdown(
                                           id=f"edges_options_season",
                                           options=[
                                               {
                                                   "label": f"Season {s}", "value": s
                                               } for s in sorted(seasons)
                                           ],
                                           multi=True
                                       ),
                                   )
                               ]
                           )
                       ] + extra_edge_properties
        return data_layout


class RatingsExplorer(BaseWidget):

    def __init__(self, network: BaseNetwork, **kwargs):
        self.main_network = network
        self.reduced_color_scale = np.random.choice(
            px.colors.qualitative.Alphabet,
            self.main_network.get_number_of_teams()
        )
        super().__init__(app_name="network_explorer", **kwargs)

    def build_layout(self):
        self.app.layout = dbc.Container(
            [
                dbc.Row(
                    dbc.Col(html.H1("Ratings explorer"), width=6),
                    justify='center'
                ),
                dbc.Row(
                    id="rating-filters",
                    children=[
                        dbc.Col(
                            id="teams-filter-col",
                            children=dcc.Dropdown(
                                id="dropdown-teams",
                                placeholder="Select teams...",
                                options=[
                                    {
                                        "label": f"Team {team_id}",
                                        "value": team_id
                                    } for team_id in self.main_network.data.nodes
                                ],
                                value=None,
                                multi=True
                            ),
                        )
                    ]
                ),
                dbc.Row(
                    children=[
                        dbc.Col(
                            id="ratings-filter-col",
                            children=dcc.Dropdown(
                                id="dropdown-ratings",
                                placeholder="Select ratings...",
                                options=[
                                    {
                                        "label": r,
                                        "value": r
                                    } for r in self.main_network.get_rankings()
                                ],
                                multi=True
                            ), width=6
                        ),
                        dbc.Col(
                            id="seasons-filter-col",
                            children=html.Div(
                                [
                                    "From season ",
                                    dcc.Input(
                                        id="from-season-input",
                                        type="number",
                                        debounce=True,
                                        min=1,
                                        max=self.main_network.seasons,
                                        value=1
                                    ),
                                    " to season ",
                                    dcc.Input(
                                        id="to-season-input",
                                        type="number",
                                        debounce=True,
                                        min=1,
                                        max=self.main_network.seasons,
                                        value=self.main_network.seasons
                                    )
                                ]
                            ),
                            width=6
                        )
                    ]
                ),
                dbc.Row(
                    justify="center",
                    children=[
                        dbc.Col(
                            children=dcc.Graph(id='ratings_chart'),
                            width=6
                        ),
                        dbc.Col(
                            children=[
                                dbc.Button(id='print-button', children="Print"),
                                dcc.Graph(id='ratings_chart_print')
                            ],
                            width=6
                        ),

                    ]
                )
            ],
            fluid=True
        )

    def configure_callbacks(self):
        @self.app.callback(Callback.Output('ratings_chart', 'figure'),
                           [Callback.Input('dropdown-teams', 'value'),
                            Callback.Input('dropdown-ratings', 'value'),
                            Callback.Input('from-season-input', 'value'),
                            Callback.Input('to-season-input', 'value')])
        def update_ratings_overview(teams, ratings, from_season, to_season):
            teams = teams or []
            return create_ratings_charts(
                self.main_network,
                ratings=ratings,
                seasons=[s - 1 for s in range(from_season, to_season + 1)],
                reduced_color_scale=self.reduced_color_scale,
                show_trend=False,
                selected_teams=teams
            )

        @self.app.callback(
            Callback.Output('ratings_chart_print', 'figure'),
            [Callback.Input('print-button', 'n_clicks')],
            [Callback.State('dropdown-teams', 'value'),
             Callback.State('dropdown-ratings', 'value'),
             Callback.State('from-season-input', 'value'),
             Callback.State('to-season-input', 'value')]
        )
        def print_ratings_chart(clicks, teams, ratings, from_season, to_season):
            if clicks is None:
                raise PreventUpdate
            return publication_chart(
                self.main_network,
                ratings=ratings,
                seasons=[s - 1 for s in range(from_season, to_season + 1)],
                selected_teams=teams,
            )
