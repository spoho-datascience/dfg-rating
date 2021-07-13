import dash
import numpy as np
import plotly.express as px
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_cytoscape as cyto
import dash.dependencies as Callback
import pandas as pd
import plotly.io as pio
from dash.exceptions import PreventUpdate

from dfg_rating.logic import controller
from dfg_rating.model.evaluators.profitability import BettingReturnsEvaluator
from dfg_rating.viz.charts import create_ratings_charts, publication_chart, accumulated_betting_chart
from dfg_rating.viz.network import create_network_figure, network_to_cyto, cyto_stylesheet, network_to_cyto_serialized, \
    custom_cyto_network
from dfg_rating.viz import tables


def init():
    cyto.load_extra_layouts()
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SANDSTONE])
    app.title = "DFG Rating"
    main_controller = controller.Controller()
    main_controller.run_demo()
    pio.templates.default = "plotly_white"

    layout = network_gui(app, 'test_network', main_controller)

    app.layout = html.Div(
        children=dbc.Container(
            [
                dbc.Row(
                    dbc.Col(html.H1('DFG Rating Analysis GUI', style={"textAlign": "center"}),
                            width=4),
                    justify='center'
                )
            ] + layout,
            fluid=True
        )
    )

    app.run_server(debug=True, port=8001)
    return True


def network_gui(app, network_name, mc):
    @app.callback(Callback.Output('network_cyto', 'layout'),
                  [Callback.Input('dropdown-layout', 'value')])
    def update_cytoscape_layout(layout):
        return {'name': layout}

    @app.callback(
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

    elements = network_to_cyto(mc.networks[network_name])
    # elements = custom_cyto_network()
    layout = [
        dbc.Row(
            children=[
                dbc.Col(
                    children=[
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
                        dbc.Button(
                            id="btn-download",
                            children="Download PNG"
                        )
                    ],
                    width=4
                ),
                dbc.Col(
                    children=cyto.Cytoscape(
                        id="network_cyto",
                        elements=elements,
                        stylesheet=cyto_stylesheet,
                        style={
                            "height": "95vh",
                            'width': '100%'
                        }
                    ),
                    width=8
                )
            ]
        )
    ]

    return layout


def ratings_gui(app, mc):
    reduced_color_scale = np.random.choice(
        px.colors.qualitative.Alphabet,
        mc.networks["test_network"].get_number_of_teams()
    )
    @app.callback(Callback.Output('ratings_chart', 'figure'),
                  [Callback.Input('dropdown-teams', 'value'),
                   Callback.Input('dropdown-ratings', 'value'),
                   Callback.Input('from-season-input', 'value'),
                   Callback.Input('to-season-input', 'value')])
    def update_ratings_overview(teams, ratings, from_season, to_season):
        teams = teams or []
        return create_ratings_charts(
            mc.networks['test_network'],
            ratings=ratings,
            seasons=[s-1 for s in range(from_season, to_season + 1)],
            reduced_color_scale=reduced_color_scale,
            show_trend=True,
            selected_teams=teams
        )
    @app.callback(
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
            mc.networks['test_network'],
            ratings=ratings,
            seasons=[s-1 for s in range(from_season, to_season + 1)],
            selected_teams=teams,
        )
    layout = [
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
                            } for team_id in mc.networks["test_network"].data.nodes
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
                            } for r in mc.get_ranking_list("test_network")
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
                                max=mc.networks['test_network'].seasons,
                                value=1
                            ),
                            " to season ",
                            dcc.Input(
                                id="to-season-input",
                                type="number",
                                debounce=True,
                                min=1,
                                max=mc.networks['test_network'].seasons,
                                value=mc.networks['test_network'].seasons
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
                    children=dcc.Graph(id='ratings_chart',
                                       figure=create_ratings_charts(mc.networks['test_network'],
                                                                    ratings=["true_rating"],
                                                                    reduced_color_scale=reduced_color_scale,
                                                                    show_trend=True)),
                    width=6
                )
            ]
        ),
        dbc.Row(
            children=[
                dbc.Col(
                    children=dcc.Graph(id='ratings_chart_print',
                                       figure=publication_chart(mc.networks['test_network'],
                                                                ratings=["function_rating"])),
                    width=6
                ),
                dbc.Col(
                    dbc.Button(id='print-button', children="Print"),
                    width=6
                )
            ],
            justify="justify"
        )
    ]

    return layout


def forecasts_gui(app, mc):
    bettings_data = mc.profitability_study(
        "test_network",
        BettingReturnsEvaluator(outcomes=['home', 'draw', 'away']),
        ["simple_bookmaker"],
        ["elo_bettor"],
    )
    df = pd.DataFrame(bettings_data)
    layout = [
        dbc.Row(
            justify="center",
            children=[
                dbc.Col(
                    id="betting_chart_col",
                    children=html.Div(
                        dcc.Graph(
                            id="betting_chart",
                            figure=accumulated_betting_chart(bettings_data)
                        )
                    ),
                    width=6
                )
            ]
        ),
        dbc.Row(
            children=[
                dbc.Col(
                    id='bettings-explore',
                    children=html.Div(tables.bettings_tables(df)),
                ),
            ]
        )
    ]
    return layout
