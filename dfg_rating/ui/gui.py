import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.io as pio

from dfg_rating.logic import controller
from dfg_rating.viz.charts import create_ratings_charts
from dfg_rating.viz.network import create_network_figure


def init():
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SANDSTONE])
    app.title = "DFG Rating"
    main_controller = controller.Controller()
    main_controller.run_demo()
    pio.templates.default = "plotly_white"

    app.layout = html.Div(
        children=dbc.Container([
            dbc.Row(
                dbc.Col(html.H1('DFG Rating Analysis GUI'), width=4),
                justify='center'
            ),
            dbc.Row(
                children=[
                    dbc.Col(
                        children=dcc.Graph(id="network_graph", figure=create_network_figure(main_controller.networks['test_network'])),
                        width=6
                    ),
                    dbc.Col(
                        children=dcc.Graph(id='ratings_chart', figure=create_ratings_charts(main_controller.networks['test_network'])),
                        width=6
                    )
                ]
            )
        ], fluid=True)
    )
    app.run_server(debug=True)
    return True
