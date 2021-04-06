import numpy as np
import plotly.express as px
from dash.exceptions import PreventUpdate
from jupyter_dash import JupyterDash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash.dependencies as Callback

from dfg_rating.model.network.base_network import BaseNetwork
from dfg_rating.viz.charts import create_ratings_charts, publication_chart


class BaseWidget:
    def __init__(self, app_name=__name__, **kwargs):
        self.app = JupyterDash(app_name, external_stylesheets=[dbc.themes.SANDSTONE], **kwargs)
        self.build_layout()
        self.configure_callbacks()

    def run(self, mode='inline'):
        self.app.run_server(mode=mode)

    def build_layout(self):
        self.app.layout = html.Div(
            html.H1("DFG Rating widgets library for Jupyter Notebooks")
        )

    def configure_callbacks(self):
        pass


class NetworkExplorer(BaseWidget):

    def __init__(self):
        super().__init__(app_name="network_explorer")

    def build_layout(self):
        pass

    def configure_callbacks(self):
        pass


class RatingsExplorer(BaseWidget):

    def __init__(self, network: BaseNetwork):
        self.main_network = network
        self.reduced_color_scale = np.random.choice(
            px.colors.qualitative.Alphabet,
            self.main_network.get_number_of_teams()
        )
        super().__init__(app_name="network_explorer")

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
                        )
                    ]
                ),
                dbc.Row(
                    children=[
                        dbc.Col(
                            children=dcc.Graph(id='ratings_chart_print'),
                            width=6
                        ),
                        dbc.Col(
                            dbc.Button(id='print-button', children="Print"),
                            width=6
                        )
                    ],
                    justify="justify"
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
