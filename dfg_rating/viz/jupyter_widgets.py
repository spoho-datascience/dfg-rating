from operator import indexOf

import numpy as np
import plotly.express as px
import dash
from dash.exceptions import PreventUpdate
from jupyter_dash import JupyterDash
import dash_core_components as dcc
import dash_cytoscape as cyto
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash.dependencies as Callback
import dash_daq as daq

import pandas as pd

from dfg_rating.model.network.base_network import BaseNetwork
from dfg_rating.viz import tables
from dfg_rating.viz.charts import create_ratings_charts, publication_chart, avg_rating_chart, rating_metrics_chart, teams_rating_chart


class BaseWidget:
    def __init__(self, app_name=__name__, **kwargs):
        self.offline = kwargs.pop('offline', False)
        self.app = dash.Dash(
            app_name, external_stylesheets=[dbc.themes.SANDSTONE]
        ) if self.offline else JupyterDash(
            app_name, external_stylesheets=[dbc.themes.SANDSTONE], **kwargs
        )
        self.build_layout()
        self.configure_callbacks()

    def run(self, mode='inline', **kwargs):
        self.app.run_server(**kwargs) if self.offline else self.app.run_server(mode=mode, **kwargs)

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
                    # 'label': 'data(label)',
                    'background-color': 'gray'
                }
            },
            {
                'selector': 'edge',
                'style': {
                    'label': 'data(label)',
                    'curve-style': 'bezier',
                    'target-arrow-shape': 'triangle',
                    'target-arrow-color': 'lightgray',
                    'line-color': 'lightgray'
                }
            },
            {
                'selector': '.inactive',
                'style': {
                    "line-color": 'lightgray',
                    'target-arrow-color': 'gray',
                    "line-style": 'dashed'
                }
            }
        ]
        ratings = self.network.export_ratings()
        cyto_elements, analysis_dict, evaluation_dict = self.network_to_cyto()
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
                                    value='grid'
                                ),
                                html.Br(),
                                dbc.Button(
                                    id="btn-download",
                                    children="Download network as PNG"
                                ),
                                html.Br(),
                                dbc.Row(dbc.Col(daq.ToggleSwitch(
                                    id="inactive_switch",
                                    value=False,
                                    label="Show inactive edges",
                                    labelPosition="right"
                                ))),
                                html.Br(),

                            ],
                            width=4
                        ),
                        dbc.Col(
                            children=cyto.Cytoscape(
                                id="cytoscape_network",
                                elements=cyto_elements,
                                stylesheet=cyto_stylesheet,
                                style={
                                    "height": "95vh",
                                    'width': '100%'
                                }
                            ),
                            width=8
                        )
                    ]
                ),
                dbc.Row(dbc.Col(dbc.Tabs(
                    [
                        dbc.Tab(
                            html.Div(tables.calendar_table(pd.DataFrame(analysis_dict))),
                            label="Schedule"
                        ),
                        dbc.Tab(
                            tables.ratings_table(ratings),
                            label="Ratings"
                        ),
                        dbc.Tab(
                            html.Div(tables.calendar_table(pd.DataFrame(analysis_dict), forecasts=True)),
                            label="Forecasts"
                        ),
                        dbc.Tab(
                            html.Div(tables.network_metrics(self.network)),
                            label="Network metrics"
                        ),
                        dbc.Tab(
                            html.Div(tables.evaluation_table(pd.DataFrame(evaluation_dict))),
                            label="Evaluation metrics"
                        )
                    ]
                )))
            ], fluid=True
        )

    def configure_callbacks(self):
        @self.app.callback([Callback.Output('cytoscape_network', 'layout'),
                            Callback.Output('cytoscape_network', 'elements'),
                            Callback.Output('kalender-table', 'data')],
                           [Callback.Input('dropdown-layout', 'value'),
                            Callback.Input('inactive_switch', 'value'),
                            Callback.Input("nodes_options_id", "value"),
                            Callback.Input("edges_options_season", "value"),
                            Callback.Input({'type': 'nodes_filter', 'index': Callback.ALL}, 'value'),
                            Callback.Input({'type': 'edges_filter', 'index': Callback.ALL}, 'value')])
        def update_cytoscape_layout(layout, input_show_inactive, id_filter, season_filter, nodes_filter, edges_filter):
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

            cyto_elements, calendar_info, evaluation_dict = self.network_to_cyto(filter_nodes, filter_edges, input_show_inactive)
            return {'name': layout}, cyto_elements, pd.DataFrame(calendar_info).to_dict('records')

        @self.app.callback(
            Callback.Output("cytoscape_network", "generateImage"),
            [
                Callback.Input("btn-download", "n_clicks")
            ],
            Callback.State("cytoscape_network", "imageData")
        )
        def get_image(btn_clicks, image_data):
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
                'action': action,
                'filename': "export"
            }

    def network_to_cyto(self, nodes_filter={}, edges_filter={}, show_inactive=False):
        elements = []
        list_of_ids = nodes_filter.get('id', [n for n in self.network.data.nodes()])
        analysis_dict = []
        evaluation_dict = []
        number_of_clusters = self.network.number_of_clusters or 1
        nodes_added_to_elements = []
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
            if (node1 not in nodes_added_to_elements) and (self.network.data.degree(node1) >= 0):
                elements += [
                    {
                        "data": {
                            "id": node1,
                            "label": f"{self.network.data.nodes[node1].get('name', node1)}",
                        },
                        "classes": f"cluster{node1}"
                    }
                ]
                nodes_added_to_elements.append(node1)
            if (node2 not in nodes_added_to_elements) and (self.network.data.degree(node2) >= 0):
                elements += [
                    {
                        "data": {
                            "id": node2,
                            "label": f"{self.network.data.nodes[node2].get('name', node2)}",
                        },
                        "classes": f"cluster{node2}"
                    }
                ]
                nodes_added_to_elements.append(node2)
            if any(self.network.data.degree(n) < 0 for n in [node1, node2]):
                continue
            if (edge_info.get('state', 'active') == 'active') or show_inactive:
                elements += [
                    {
                        "data": {
                            "id": f"{node2}_{node1}_{edge_info['season']}_{edge_info['round']}",
                            "label": "",
                            "source": node2, "target": node1
                        },
                        "classes": edge_info.get('state', 'active')
                    }
                ]
                new_dict = {
                    "HomeTeam": self.network.data.nodes[node2].get("name", node2),
                    "AwayTeam": self.network.data.nodes[node1].get("name", node1),
                    "Season": edge_info.get('season', None),
                    "Round": edge_info.get('round', None),
                    "Result": edge_info.get('winner', None),
                    "State": edge_info.get('state', 'active')
                }
                for f_name, f in edge_info.get('forecasts', {}).items():
                    new_dict[f"{f_name}#"] = [f"{outcome:.2f} - " for outcome in f.probabilities]
                analysis_dict.append(new_dict)
                for evaluator_name, evaluator in edge_info.get('metrics', {}).items():
                    evaluation_dict.append(
                        {
                            "HomeTeam": self.network.data.nodes[node2].get("name", node2),
                            "AwayTeam": self.network.data.nodes[node1].get("name", node1),
                            "Season": edge_info.get('season', None),
                            "Round": edge_info.get('round', None),
                            "Result": edge_info.get('winner', None),
                            "State": edge_info.get('state', 'active'),
                            "Metric": evaluator_name,
                            "Value": evaluator
                        }
                    )
        return elements, analysis_dict, evaluation_dict

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
                            id="nodes_options_id",
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
                                        "label": f"Team {team_id}{self.main_network.data.nodes[team_id].get('name', '')}",
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
                                        min=0,
                                        max=max(self.main_network.get_seasons()),
                                    ),
                                    " to season ",
                                    dcc.Input(
                                        id="to-season-input",
                                        type="number",
                                        debounce=True,
                                        min=1,
                                        max=max(self.main_network.get_seasons()) + 1,
                                        value=max(self.main_network.get_seasons()),
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
                            width=12
                        )
                    ]
                ),
                dbc.Row(
                    justify="center",
                    children=[
                        dbc.Col(
                            children=dcc.Graph(id='teams-ratings'),
                            width=6
                        ),
                        dbc.Col(
                            children=[
                                dbc.Button(id='print-button', children="Print"),
                                dcc.Graph(id='ratings_chart_print', config={
                                    'toImageButtonOptions': {
                                        'format': 'svg',  # one of png, svg, jpeg, webp
                                        'filename': 'rating_chart',
                                        'scale': 1  # Multiply title/legend/axis/canvas sizes by this factor
                                    }
                                })
                            ],
                            width=6
                        ),
                    ]
                )
            ],
            fluid=True
        )

    def configure_callbacks(self):
        @self.app.callback([Callback.Output('ratings_chart', 'figure'),
                            Callback.Output('teams-ratings', 'figure')],
                           [Callback.Input('dropdown-teams', 'value'),
                            Callback.Input('dropdown-ratings', 'value'),
                            Callback.Input('from-season-input', 'value'),
                            Callback.Input('to-season-input', 'value')])
        def update_ratings_overview(teams, ratings, from_season, to_season):
            if any(attribute is None for attribute in [from_season, to_season]):
                raise PreventUpdate
            teams = teams or []
            ratings = ratings or ['true_rating']
            ratings_chart_figure = create_ratings_charts(
                self.main_network,
                ratings=ratings,
                seasons=[s - 1 for s in range(from_season, to_season + 1)],
                reduced_color_scale=self.reduced_color_scale,
                show_trend=False,
                selected_teams=teams
            )
            teams_rating_figure = teams_rating_chart(
                self.main_network,
                rating=ratings[-1],
                seasons=[s - 1 for s in range(from_season, to_season + 1)],
                selected_teams=teams,
            )
            return ratings_chart_figure, teams_rating_figure

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


class RatingsEvaluation(BaseWidget):

    def __init__(self, network: BaseNetwork, **kwargs):
        self.main_network = network
        super().__init__(app_name="ratings_evaluation", **kwargs)

    def build_layout(self):
        self.app.layout = dbc.Container(
            [
                dbc.Row(
                    dbc.Col(html.H1("Results"), width=6),
                    justify='center'
                ),
                dbc.Row(
                    id="rating-filters",
                    children=[
                        dbc.Col(
                            id="teams-filter-col",
                            children=dcc.Dropdown(
                                id="dropdown-teams",
                                placeholder="Teams",
                                options=[
                                    {
                                        "label": f"Team {team_id}",
                                        "value": team_id
                                    } for team_id in self.main_network.data.nodes
                                ],
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
                                placeholder="Ratings",
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
                            children=dcc.Graph(id='rating_values'),
                            width=6
                        ),
                        dbc.Col(
                            children=[
                                dcc.Graph(id='rating_metrics')
                            ],
                            width=6
                        ),

                    ]
                )
            ],
            fluid=True
        )

    def configure_callbacks(self):
        @self.app.callback([Callback.Output('rating_values', 'figure'),
                            Callback.Output('rating_metrics', 'figure')],
                           [Callback.Input('dropdown-teams', 'value'),
                            Callback.Input('dropdown-ratings', 'value'),
                            Callback.Input('from-season-input', 'value'),
                            Callback.Input('to-season-input', 'value')])
        def update_rating_charts(teams, ratings, from_season, to_season):
            ratings = ratings or ['true_rating']
            rating_values_figure = avg_rating_chart(
                self.main_network,
                ratings_list=ratings,
                seasons=[s - 1 for s in range(from_season, to_season + 1)],
                selected_teams=teams
            )
            rating_metrics_figure = rating_metrics_chart(
                self.main_network,
                ratings_list=[r for r in ratings if r != 'true_rating'],
                seasons=[s - 1 for s in range(from_season, to_season + 1)],
                selected_teams=teams
            )
            return rating_values_figure, rating_metrics_figure


class DegreeExplorer(BaseWidget):

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
                    # 'label': 'data(label)',
                    "width": "mapData(score, 10, 40, 10, 150)",
                    "height": "mapData(score, 10, 40, 10, 150)",
                    'background-color': 'black'
                }
            },
            {
                'selector': 'edge',
                'style': {
                    'label': 'data(label)',
                    'curve-style': 'bezier',
                    'target-arrow-shape': 'triangle',
                    'target-arrow-color': 'ligthgray',
                    'line-color': 'lightgray'
                }
            },
            {
                'selector': '.inactive',
                'style': {
                    "line-color": 'lightgray',
                    'target-arrow-color': 'gray',
                    "line-style": 'dashed'
                }
            },
            {
                'selector': '.cluster0',
                'style': {
                    'background-color': 'blue'
                }
            },
            {
                'selector': '.cluster1',
                'style': {
                    'background-color': 'red'
                }
            },
            {
                'selector': '.cluster2',
                'style': {
                    'background-color': 'yellow'
                }
            },
            {
                'selector': '.cluster3',
                'style': {
                    'background-color': 'green'
                }
            },
            {
                'selector': '.cluster4',
                'style': {
                    'background-color': 'gray'
                }
            },
            {
                'selector': '.cluster5',
                'style': {
                    'background-color': 'brown'
                }
            },
            {
                'selector': '.cluster6',
                'style': {
                    'background-color': 'purple'
                }
            }
        ]
        ratings = self.network.export_ratings()
        cyto_elements, analysis_dict, evaluation_dict = self.network_to_cyto()
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
                                    value='grid'
                                ),
                                html.Br(),
                                dbc.Button(
                                    id="btn-download",
                                    children="Download network as PNG"
                                ),
                                html.Br(),
                                dbc.Row(dbc.Col(daq.ToggleSwitch(
                                    id="inactive_switch",
                                    value=False,
                                    label="Show inactive edges",
                                    labelPosition="right"
                                ))),
                                html.Br(),

                            ],
                            width=4
                        ),
                        dbc.Col(
                            children=cyto.Cytoscape(
                                id="cytoscape_network",
                                elements=cyto_elements,
                                stylesheet=cyto_stylesheet,
                                style={
                                    "height": "95vh",
                                    'width': '100%'
                                }
                            ),
                            width=8
                        )
                    ]
                ),
                dbc.Row(dbc.Col(dbc.Tabs(
                    [
                        dbc.Tab(
                            html.Div(tables.calendar_table(pd.DataFrame(analysis_dict))),
                            label="Schedule"
                        ),
                        dbc.Tab(
                            tables.ratings_table(ratings),
                            label="Ratings"
                        ),
                        dbc.Tab(
                            html.Div(tables.calendar_table(pd.DataFrame(analysis_dict), forecasts=True)),
                            label="Forecasts"
                        ),
                        dbc.Tab(
                            html.Div(tables.network_metrics(self.network)),
                            label="Network metrics"
                        ),
                        dbc.Tab(
                            html.Div(tables.evaluation_table(pd.DataFrame(evaluation_dict))),
                            label="Evaluation metrics"
                        )
                    ]
                )))
            ], fluid=True
        )

    def configure_callbacks(self):
        @self.app.callback([Callback.Output('cytoscape_network', 'layout'),
                            Callback.Output('cytoscape_network', 'elements'),
                            Callback.Output('kalender-table', 'data')],
                           [Callback.Input('dropdown-layout', 'value'),
                            Callback.Input('inactive_switch', 'value'),
                            Callback.Input("nodes_options_id", "value"),
                            Callback.Input("edges_options_season", "value"),
                            Callback.Input({'type': 'nodes_filter', 'index': Callback.ALL}, 'value'),
                            Callback.Input({'type': 'edges_filter', 'index': Callback.ALL}, 'value')])
        def update_cytoscape_layout(layout, input_show_inactive, id_filter, season_filter, nodes_filter, edges_filter):
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

            cyto_elements, calendar_info, evaluation_dict = self.network_to_cyto(filter_nodes, filter_edges, input_show_inactive)
            return {'name': layout}, cyto_elements, pd.DataFrame(calendar_info).to_dict('records')

        @self.app.callback(
            Callback.Output("cytoscape_network", "generateImage"),
            [
                Callback.Input("btn-download", "n_clicks")
            ],
            Callback.State("cytoscape_network", "imageData")
        )
        def get_image(btn_clicks, image_data):
            # File type to ouput of 'svg, 'png', 'jpg', or 'jpeg' (alias of 'jpg')
            ftype = 'png'
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

    def network_to_cyto(self, nodes_filter={}, edges_filter={}, show_inactive=False):
        elements = []
        list_of_ids = nodes_filter.get('id', [n for n in self.network.data.nodes()])
        degrees = {n_id: d for n_id, d in self.network.degree(filter_active=True)}
        print(degrees)
        analysis_dict = []
        evaluation_dict = []
        number_of_clusters = self.network.number_of_clusters or 1
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
                        "score": degrees[node1],
                        "label": f"{self.network.data.nodes[node1].get('name', node1)}",
                    },
                    "classes": f"cluster{node1 % number_of_clusters}"
                },
                {
                    "data": {
                        "id": node2,
                        "score": degrees[node2],
                        "label": f"{self.network.data.nodes[node1].get('name', node2)}",
                    },
                    "classes": f"cluster{node2 % number_of_clusters}"
                },
            ]
            if (edge_info.get('state', 'active') == 'active') or show_inactive:
                elements += [
                    {
                        "data": {
                            "id": f"{node2}_{node1}_{edge_info['season']}_{edge_info['round']}",
                            "label": "",
                            "source": node2, "target": node1
                        },
                        "classes": edge_info.get('state', 'active')
                    }
                ]
                new_dict = {
                    "HomeTeam": self.network.data.nodes[node2].get("name", node2),
                    "AwayTeam": self.network.data.nodes[node1].get("name", node1),
                    "Season": edge_info.get('season', None),
                    "Round": edge_info.get('round', None),
                    "Result": edge_info.get('winner', None),
                    "State": edge_info.get('state', 'active')
                }
                for f_name, f in edge_info.get('forecasts', {}).items():
                    new_dict[f"{f_name}#"] = [f"{outcome:.2f} - " for outcome in f.probabilities]
                analysis_dict.append(new_dict)
                for evaluator_name, evaluator in edge_info.get('metrics', {}).items():
                    evaluation_dict.append(
                        {
                            "HomeTeam": self.network.data.nodes[node2].get("name", node2),
                            "AwayTeam": self.network.data.nodes[node1].get("name", node1),
                            "Season": edge_info.get('season', None),
                            "Round": edge_info.get('round', None),
                            "Result": edge_info.get('winner', None),
                            "State": edge_info.get('state', 'active'),
                            "Metric": evaluator_name,
                            "Value": evaluator
                        }
                    )
        return elements, analysis_dict, evaluation_dict

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
                            id="nodes_options_id",
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


class ForecastExplorer(BaseWidget):

    def __init__(self, network: BaseNetwork, **kwargs):
        self.network = network
        self.extra_node_properties = kwargs.pop('node_props', [])
        self.extra_edge_properties = kwargs.pop('edge_props', [])
        self.ratings = kwargs.pop('ratings', None)
        self.forecasts = kwargs.pop('forecasts', None)
        super().__init__(app_name="network_explorer", **kwargs)

    def build_layout(self):
        self.ratings_dict = self.network.export_ratings()
        analysis_dict, evaluation_dict = self.export_network()
        self.app.layout = dbc.Container(
            [
                dbc.Row(
                    dbc.Col(
                        html.Div(tables.calendar_table(pd.DataFrame(analysis_dict), forecasts=True)),
                        width=12
                    )
                )
            ], fluid=True
        )

    def configure_callbacks(self):
        pass

    def export_network(self, nodes_filter={}, edges_filter={}, show_inactive=False):
        list_of_ids = nodes_filter.get('id', [n for n in self.network.data.nodes()])
        analysis_dict = []
        evaluation_dict = []
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
            if (edge_info.get('state', 'active') == 'active') or show_inactive:
                new_dict = {
                    "HomeTeam": self.network.data.nodes[node2].get("name", node2),
                    "AwayTeam": self.network.data.nodes[node1].get("name", node1),
                    "Season": edge_info.get('season', None),
                    "Round": edge_info.get('round', None),
                    "Result": edge_info.get('winner', None),
                    "State": edge_info.get('state', 'active')
                }
                rating_node_1 = self.ratings_dict.get(node1, {})
                rating_node_2 = self.ratings_dict.get(node2, {})
                rounds, round_values = self.network.get_rounds()
                round_pointer = indexOf(round_values, new_dict["Round"])
                if self.ratings is None:
                    for rating_node, p in [(rating_node_2, "HomeTeam"), (rating_node_1, "AwayTeam")]:
                        for r_name, r_value in rating_node.items():
                            new_dict[f"{r_name} # {p}"] = r_value.get(
                                new_dict["Season"]
                            )[round_pointer]
                else:
                    for rating_node, p in [(rating_node_2, "HomeTeam"), (rating_node_1, "AwayTeam")]:
                        for r_name in self.ratings:
                            r_value = rating_node.get(r_name)
                            new_dict[f"{r_name} # {p}"] = r_value.get(
                                new_dict["Season"]
                            )[round_pointer]

                if self.forecasts is None:
                    for f_name, f in edge_info.get('forecasts', {}).items():
                        new_dict[f"{f_name}#"] = [f"{outcome:.2f} - " for outcome in f.probabilities]

                else:
                    for f_name in self.forecasts:
                        f = edge_info.get('forecasts', {}).get(f_name, None)
                        if f is not None:
                            new_dict[f"{f_name}#"] = [f"{outcome:.2f} - " for outcome in f.probabilities]
                analysis_dict.append(new_dict)
                for evaluator_name, evaluator in edge_info.get('metrics', {}).items():
                    evaluation_dict.append(
                        {
                            "HomeTeam": self.network.data.nodes[node2].get("name", node2),
                            "AwayTeam": self.network.data.nodes[node1].get("name", node1),
                            "Season": edge_info.get('season', None),
                            "Round": edge_info.get('round', None),
                            "Result": edge_info.get('winner', None),
                            "State": edge_info.get('state', 'active'),
                            "Metric": evaluator_name,
                            "Value": evaluator
                        }
                    )
        return analysis_dict, evaluation_dict

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
                            id="nodes_options_id",
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
