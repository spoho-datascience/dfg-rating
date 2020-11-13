import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import pandas as pd


def init():
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SANDSTONE])
    app.title = "DFG Rating"

    app.layout = html.Div(
        children=[
            html.H1('DFG Rating Analysis GUI')
        ]
    )
    app.run_server(debug=True)
    return True
