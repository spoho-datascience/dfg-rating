import dash_table
import dash_html_components as html
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np

import networkx as nx
from networkx import MultiDiGraph
from dfg_rating.model import forecast

from dfg_rating.model.evaluators.accuracy import RankProbabilityScore, Likelihood, ForecastError, \
    ExpectedRankProbabilityScore
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


def calendar_table(df, forecasts=False):
    return dash_table.DataTable(
        id="kalender-table" + ("full" if forecasts else ""),
        columns=[
            {"name": ["Match", "HomeTeam"], "id": "HomeTeam"},
            {"name": ["Match", "AwayTeam"], "id": "AwayTeam"},
            {"name": ["Match", "Season"], "id": "Season"},
            {"name": ["Match", "Round"], "id": "Round"},
            {"name": ["Match", "Result"], "id": "Result"},
            {"name": ["Match", "State"], "id": "State"},
        ] + [{"name": ["Match", i], "id": i, 'type': 'numeric', 'format': {'specifier': '.2f'}} for i in
             df.columns if '#' in i],
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


def ratings_table(ratings_dict, season=1):
    df_data = []
    ratings_list = set([])
    conditional_styles = []
    for team, team_ratings in ratings_dict.items():
        ratings_list = set([])
        for rating, rating_values in team_ratings.items():
            if rating not in ['hyper_parameters']:
                ratings_list.add(rating)
                new_rating = {
                    "Team": team,
                    "Id": rating
                }
                previous_value = 1000.00
                for round_id, round_value in enumerate(rating_values.get(season, [])):
                    new_rating[f"#{round_id + 1}"] = round_value
                    if rating == "elo_rating_17":
                        if round_id > 0:
                            if round_value != previous_value:
                                conditional_styles.append({
                                    'if': {
                                        'filter_query': '{{Id}} = "elo_rating_17" && {{Team}} = {}'.format(team),
                                        'column_id': f"#{round_id + 1}"
                                    },
                                    'backgroundColor': '#3D9970',
                                    'color': 'white'
                                })
                    previous_value = round_value
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
    degree_distribution = np.array([v for k, v in n.degree()])
    layout = html.Div([
        dbc.Row(html.Div(f"Network density: {n.density(True)}")),
        dbc.Row(html.Div(f"Q1: {np.percentile(degree_distribution, 25)}")),
        dbc.Row(html.Div(f"Median: {np.percentile(degree_distribution, 50)}")),
        dbc.Row(html.Div(f"Q3: {np.percentile(degree_distribution, 75)}")),
        dbc.Row(html.Div(f"Min: {degree_distribution.min()}")),
        dbc.Row(html.Div(f"Max: {degree_distribution.max()}")),
        dbc.Row(children="----------")
    ] + [
        dbc.Row(html.Div(f"Node {node}: {d}")) for node, d in n.degree(True)
    ])
    return layout


def evaluation_table(df):
    return dash_table.DataTable(
        id="evaluation_table",
        columns=[{"name": i, "id": i} for i in df.columns],
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


def get_evaluation(network: BaseNetwork, k, abs=True, evaluators=[], extra_attributes=[], **kwargs):
    rating_name = f"elo_rating_{k}"
    forecast_name = f"elo_forecast_{k}"
    print(forecast_name)
    analysis_data = []
    add_true = kwargs.get("add_true_dimension", True)
    n_rounds, round_values = network.get_rounds()
    round_dict = {round_v: round_i for round_i, round_v in enumerate(round_values)}
    for node1, node2, edge_key, edge_info in filter(lambda match: match[3].get('state', 'active') == 'active',
                                                    network.iterate_over_games()):
        if edge_info.get('state', 'active') == 'active':
            cf = edge_info.get('forecasts', {}).get(forecast_name)
            cf_tuple = "-".join([f"{outcome:.2f}" for outcome in cf.probabilities])
            if add_true:
                tf = edge_info.get('forecasts', {}).get('true_forecast')
                tf_tuple = "-".join([f"{outcome:.2f}" for outcome in tf.probabilities])
                new_dict = {
                    "HomeTeam": network.data.nodes[node2].get("name", node2),
                    "AwayTeam": network.data.nodes[node1].get("name", node1),
                    "Season": edge_info.get('season', None),
                    "Round": edge_info.get('round', None),
                    "Day": edge_info.get('day', None),
                    "Result": edge_info.get('winner', None),
                    "TrueForecast": tf_tuple,
                    "CalculatedForecast": cf_tuple,
                    "ELO_Rating_K": k,
                }
            else:
                new_dict = {
                    "HomeTeam": network.data.nodes[node2].get("name", node2),
                    "AwayTeam": network.data.nodes[node1].get("name", node1),
                    "Season": edge_info.get('season', None),
                    "Round": edge_info.get('round', None),
                    "Day": edge_info.get('day', None),
                    "Result": edge_info.get('winner', None),
                    "CalculatedForecast": cf_tuple,
                    "ELO_Rating_K": k,
                }
            for extra_key in extra_attributes:
                new_dict[extra_key] = edge_info.get(extra_key, None)
            for key, value in kwargs.items():
                new_dict[key] = value
            for e in evaluators:
                evaluator_name = f"{rating_name}_{e}"
                new_dict[e] = edge_info.get('metrics', {}).get(evaluator_name, 0)
            if abs:
                round_pointer = round_dict.get(edge_info.get('round', 0), 0)
                if add_true:
                    home_true = network.data.nodes[node2].get(
                        'ratings', {}
                    ).get('true_rating', {}).get(0, [0])[round_pointer]
                    away_true = network.data.nodes[node1].get(
                        'ratings', {}
                    ).get('true_rating', {}).get(0, [0])[round_pointer]
                    new_dict["HomeRating"] = home_true
                    new_dict['AwayRating'] = away_true
                home_c = network.data.nodes[node2].get(
                    'ratings', {}
                ).get(rating_name, {}).get(0, [0])[round_pointer]
                away_c = network.data.nodes[node1].get(
                    'ratings', {}
                ).get(rating_name, {}).get(0, [0])[round_pointer]
                new_dict[f"Home_elo_rating"] = home_c
                new_dict[f"Away_elo_rating"] = away_c
            analysis_data.append(new_dict)
    return analysis_data


def get_league_rating_values(network: BaseNetwork, rating: str, number_of_leagues: int, **kwargs):
    rating_values = []
    list_of_arrays = {}
    for node in network.data:
        cluster_name = node % number_of_leagues
        for season, season_array in network.data.nodes[node]['ratings'][rating].items():
            list_of_arrays.setdefault(
                cluster_name, []
            ).append(season_array)
    for cluster, cluster_arrays in list_of_arrays.items():
        a = np.array(cluster_arrays)
        mean_array = a.mean(axis=0)
        for i, value in enumerate(mean_array):
            rating_values.append({
                **kwargs,
                "rating": rating,
                "cluster_name": cluster,
                "Round": i,
                "cluster_rating": value
            })
    return rating_values


def get_evaluation_list(rating_name, forecast_name):
    rps = RankProbabilityScore(
        outcomes=['home', 'draw', 'away'],
        forecast_name=forecast_name
    )
    likelihood = Likelihood(
        outcomes=['home', 'draw', 'away'],
        forecast_name=forecast_name
    )
    forecast_error = ForecastError(
        outcomes=['home', 'draw', 'away'],
        forecast_name=forecast_name
    )
    true_rps = RankProbabilityScore(
        outcomes=['home', 'draw', 'away'],
        forecast_name="true_forecast"
    )
    exp_rps = ExpectedRankProbabilityScore(
        outcomes=['home', 'draw', 'away'],
        forecast_name=forecast_name
    )
    min_rps = ExpectedRankProbabilityScore(
        outcomes=['home', 'draw', 'away'],
        forecast_name="true_forecast"
    )
    evaluation_list = [
        (rps, f"{rating_name}_RPS"),
        (true_rps, f"{rating_name}_TrueRPS"),
        (likelihood, f"{rating_name}_Likelihood"),
        (forecast_error, f"{rating_name}_ForecastError"),
        (exp_rps, f"{rating_name}_ExpectedRPS"),
        (min_rps, f"{rating_name}_Forecastability")
    ]
    return evaluation_list
