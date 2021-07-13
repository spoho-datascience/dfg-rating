import dash_table
import dash_html_components as html
import dash_bootstrap_components as dbc
import pandas as pd

import networkx as nx
from networkx import MultiDiGraph

from dfg_rating.model.network.base_network import BaseNetwork

pd.options.display.float_format = '${:.2f}'.format


def bettings_tables(df):
    return dash_table.DataTable(
        id="bettings-table",
        columns=[
            {"name": ["Match", "HomeTeam"], "id": "HomeTeam"},
            {"name": ["Match", "AwayTeam"], "id": "AwayTeam"},
            {"name": ["Match", "Season"], "id": "Season"},
            {"name": ["Match", "Round"], "id": "Round"},
            {"name": ["Match", "Result"], "id": "Result"},
            {"name": ["True forecast", "Home"], "id": "true_forecast#home"},
            {"name": ["True forecast", "Draw"], "id": "true_forecast#draw"},
            {"name": ["True forecast", "Away"], "id": "true_forecast#away"},
            {"name": ["Simple bookmaker odds", "Home"], "id": "odds#home"},
            {"name": ["Simple bookmaker odds", "Draw"], "id": "odds#draw"},
            {"name": ["Simple bookmaker odds", "Away"], "id": "odds#away"},
            {"name": ["ELO forecast", "Home"], "id": "elo_forecast#home"},
            {"name": ["ELO forecast", "Draw"], "id": "elo_forecast#draw"},
            {"name": ["ELO forecast", "Away"], "id": "elo_forecast#away"},
            {"name": ["ELO bets", "Home"], "id": "bet#home"},
            {"name": ["ELO bets", "Draw"], "id": "bet#draw"},
            {"name": ["ELO bets", "Away"], "id": "bet#away"},
            {"name": ["Expected returns", "Home"], "id": "expected#bet#home"},
            {"name": ["Expected returns", "Draw"], "id": "expected#bet#draw"},
            {"name": ["Expected returns", "Away"], "id": "expected#bet#away"},
            {"name": ["Actual returns", "Home"], "id": "return#bet#home"},
            {"name": ["Actual returns", "Draw"], "id": "return#bet#draw"},
            {"name": ["Actual returns", "Away"], "id": "return#bet#away"},
        ],
        merge_duplicate_headers=True,
        data=df.to_dict('records'),
        style_header={
            'backgroundColor': 'white',
            'fontWeight': 'bold',
        },
        style_cell={
            'textAlign': 'left',
            'whiteSpace': 'pre-line',
            'height': 'auto',
        },
        sort_action='native',
        page_size=20,
        page_action='native',
        filter_action='native'
    )


def calendar_table(df):
    return dash_table.DataTable(
        id="kalender-table",
        columns=[
            {"name": ["Match", "HomeTeam"], "id": "HomeTeam"},
            {"name": ["Match", "AwayTeam"], "id": "AwayTeam"},
            {"name": ["Match", "Season"], "id": "Season"},
            {"name": ["Match", "Round"], "id": "Round"},
            {"name": ["Match", "Result"], "id": "Result"},
            {"name": ["Match", "State"], "id": "State"},
        ],
        merge_duplicate_headers=True,
        data=df.to_dict('records'),
        style_header={
            'backgroundColor': 'white',
            'fontWeight': 'bold',
        },
        style_cell={
            'textAlign': 'left',
            'whiteSpace': 'pre-line',
            'height': 'auto',
        },
        style_data_conditional=[
            {
                'if': {
                    'filter_query': '{State} = "inactive"',
                },
                'backgroundColor': '#F47174',
                'color': 'white'
            },
        ],
        sort_action='native',
        page_size=20,
        page_action='native',
        filter_action='native'
    )


def ratings_table(ratings_dict, season=0):
    df_data = []
    ratings_list = set([])
    first_proc = True
    conditional_styles = []
    for team, team_ratings in ratings_dict.items():
        for rating, rating_values in team_ratings.items():
            if rating not in ['hyper_parameters']:
                ratings_list.add(rating)
                new_rating = {
                    "Team": team,
                    "Id": rating
                }
                previous_value = 1000.00
                for round_id, round_value in enumerate(rating_values[season]):
                    new_rating[f"#{round_id + 1}"] = round_value
                    if (rating != "true_rating") and first_proc:
                        if round_id > 0:
                            if round_value != previous_value:
                                conditional_styles.append({
                                    'if': {
                                        'filter_query': '{{Id}} = "elo_rating" && {{Team}} = {}'.format(team),
                                        'column_id': f"#{round_id + 1}"
                                    },
                                    'backgroundColor': '#3D9970',
                                    'color': 'white'
                                })
                    previous_value = round_value

                first_proc = rating == "true_rating"
                df_data.append(new_rating)
    ratings_df = pd.DataFrame(df_data)
    export_df = ratings_df.to_dict('records')
    for rating in ratings_list:
        mean_row = ratings_df[ratings_df['Id'] == rating].mean().to_dict()
        mean_row["Team"] = -1,
        mean_row["Id"] = f"mean_{rating}"
        export_df.append(mean_row)
    return html.Div(dash_table.DataTable(
        id="ratings-table",
        columns=[{"name": i, "id": i, 'type': 'numeric', 'format': {'specifier': '.2f'}} for i in ratings_df.columns],
        data=export_df,
        fixed_columns={'headers': True, 'data': 2},
        style_table={'minWidth': '100%'},
        style_header={
            'backgroundColor': 'white',
            'fontWeight': 'bold',
        },
        style_cell={
            'textAlign': 'left',
            'minWidth': "60px",
        },
        style_data_conditional=conditional_styles,
        sort_action='native',
        page_action='native',
        filter_action='native',
        css=[{'selector': '.row', 'rule': 'margin: 0'}, {'selector': '.row', 'rule': 'flex-wrap: nowrap'}]
    ))


def network_metrics(n: BaseNetwork):
    graph = n.data.edge_subgraph([(edge[0], edge[1], edge[2]) for edge in n.data.edges(keys=True, data=True) if edge[3]['state'] == 'active'])
    layout = html.Div([
        dbc.Row(html.Div(f"Network density: {nx.density(graph)}")),
    ] + [dbc.Row(html.Div(f"Node {node}: {d}")) for node, d in graph.degree()])
    return layout
