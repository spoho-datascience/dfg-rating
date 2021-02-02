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
from dfg_rating.viz.charts import create_ratings_charts
from dfg_rating.viz.network import create_network_figure, network_to_cyto, cyto_stylesheet, network_to_cyto_serialized


def init():
    cyto.load_extra_layouts()
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SANDSTONE])
    app.title = "DFG Rating"
    main_controller = controller.Controller()
    main_controller.run_demo()
    pio.templates.default = "plotly_white"
    elements = network_to_cyto(main_controller.networks['test_network'])

    reduced_color_scale = np.random.choice(
        px.colors.qualitative.Alphabet,
        main_controller.networks["test_network"].get_number_of_teams()
    )
    reduced_color_scale = px.colors.qualitative.Alphabet

    app.layout = html.Div(
        children=dbc.Container([
            dbc.Row(
                dbc.Col(html.H1('DFG Rating Analysis GUI', style={"text-align": "center"}), width=4),
                justify='center'
            ),
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
            ),
            """
            dbc.Row(
                children=[
                    dbc.Col(
                        children=dcc.Graph(id='ratings_chart',
                                           figure=create_ratings_charts(main_controller.networks['test_network'], ratings=["true_rating"], reduced_color_scale=reduced_color_scale, show_trend=True)),
                        width=6
                    ),
                    dbc.Col(
                        children=dcc.Graph(id='ratings_chart_dos',
                                           figure=create_ratings_charts(main_controller.networks['test_network'], ratings=["function_rating"], reduced_color_scale=reduced_color_scale)),
                        width=6
                    )
                ]
            )"""
        ], fluid=True)
    )

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

    app.run_server(debug=True, port=8001)
    return True
