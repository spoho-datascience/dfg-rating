"""Module of helpers building charts and data visualizations
"""
from typing import List

import plotly.graph_objects as go
import plotly.express as px
import numpy as np

from dfg_rating.model.network.base_network import BaseNetwork


def create_ratings_charts(
        network: BaseNetwork,
        ratings: [str] = ['true_rating'],
        seasons: [int] = None,
        reduced_color_scale: List[str] = px.colors.qualitative.Light24,
        show_trend=False,
        selected_teams=[]
) -> go.Figure:
    """Rating chart evolution

    Given a certain rating name and a network. It creates a figure with the rating evolution for all the teams
    in the network. The color scale can be also specified. The figure contains each rating values per round of
    the network season and the trend evolution of each rating.

    Args:
        network: Sport network of teams and matches.
        rating: Optional; Rating name to plot.
        color_scale: Optional; Color scale for the figure.

    Returns:
        A dict-based plotly Figure object with the rating chart for all the teams in the network.

    """
    fig = go.Figure()
    if len(selected_teams) == 0:
        selected_teams = network.data.nodes
    ratings = ratings or ['true_rating']
    seasons = seasons or []
    if len(seasons) == 0:
        seasons = range(network.seasons)
    for team in selected_teams:
        for rating in ratings:
            total_rating_array = np.array([])
            total_trend_x = np.array([])
            total_trend_y = np.array([])
            for season in seasons:
                rating_array = network.data.nodes[team].get('ratings', {}).get(rating, {}).get(season, [])
                total_rating_array = np.concatenate((total_rating_array, np.array(rating_array)))
                rating_hp = network.data.nodes[team].get('ratings', {}).get("hyper_parameters", {}).get(rating, {}).get(
                    season, {})
                trend_x = np.array(range(len(rating_array)), dtype=np.float) + (len(rating_array) * season)
                total_trend_x = np.concatenate((total_trend_x, trend_x))
                to_zero_trend_x = np.array([i for i in range(len(trend_x))])
                trend_y = to_zero_trend_x * rating_hp.get('trends', [0])[0] * network.days_between_rounds + \
                          rating_hp.get('starting_points', [0])[0]
                total_trend_y = np.concatenate((total_trend_y, trend_y))

            fig.add_trace(go.Scatter(
                x=[i for i in range(len(total_rating_array))],
                y=total_rating_array,
                mode='lines',
                line=dict(
                    color=reduced_color_scale[team],
                    width=3.5
                ) if rating != 'true_rating' else dict(
                    color=reduced_color_scale[team],
                    width=1.5
                ),
                name=f"{rating}-Team {team}"
            ))
            if show_trend and (rating == 'true_rating'):
                fig.add_trace(go.Scatter(
                    x=total_trend_x,
                    y=total_trend_y,
                    mode='lines',
                    line=dict(
                        width=0.5,
                        color=reduced_color_scale[team],
                    ),
                    name=f"{rating}-Trend team {team}"
                ))
    fig.update_layout(
        title="Team ratings",
        xaxis_title="League rounds",
        yaxis_title="Rating value",
    )
    return fig


def publication_chart(
        network: BaseNetwork,
        ratings: [str] = ['true_rating'],
        seasons: [int] = None,
        show_trend=True,
        show_starting=False,
        selected_teams: [int] = None
) -> go.Figure:
    fig = go.Figure()
    selected_teams = selected_teams or []
    seasons = seasons or []
    if len(selected_teams) == 0:
        selected_teams = [2]
    ratings = ratings or ['true_rating']
    if len(seasons) == 0:
        seasons = range(network.seasons)
    for team in selected_teams:
        for i_rating, rating in enumerate(ratings):
            total_rating_array = np.array([])
            total_trend_x = np.array([])
            total_trend_y = np.array([])
            for season in seasons:
                rating_array = network.data.nodes[team].get('ratings', {}).get(rating, {}).get(season, [])
                total_rating_array = np.concatenate((total_rating_array, np.array(rating_array)))
                rating_hp = network.data.nodes[team].get('ratings', {}).get("hyper_parameters", {}).get(rating, {}).get(
                    season, {})
                trend_x = np.array(range(len(rating_array)), dtype=np.float) + (len(rating_array) * season)
                total_trend_x = np.concatenate((total_trend_x, trend_x))
                to_zero_trend_x = np.array([i for i in range(len(trend_x))])
                trend_y = to_zero_trend_x * rating_hp.get('trends', [0])[0] * network.days_between_rounds + \
                          rating_hp.get('starting_points', [0])[0]
                total_trend_y = np.concatenate((total_trend_y, trend_y))

            fig.add_trace(go.Scatter(
                x=[i for i in range(len(total_rating_array))],
                y=total_rating_array,
                mode='lines',
                line=dict(color=px.colors.sequential.Greys[
                    len(px.colors.sequential.Greys) - 1 - (i_rating + i_rating + i_rating)]),
                name=rating
            ))
            if show_starting:
                fig.add_trace(go.Scatter(
                    x=[0],
                    y=[network.data.nodes[team].get('ratings', {}).get("hyper_parameters", {}).get(rating, {}).get(
                        0, {}).get('starting_points', [0])[0]],
                    mode='markers',
                    marker=dict(color=px.colors.sequential.Greys[i_rating + i_rating], size=12),
                    name="Starting point"
                ))
            if show_trend and (rating == 'true_rating'):
                fig.add_trace(go.Scatter(
                    x=total_trend_x,
                    y=total_trend_y,
                    mode='lines',
                    line=dict(
                        width=0.5,
                        color="black",
                        dash='dash'
                    ),
                    name='True rating trend'
                ))
    fig.update_layout(
        xaxis_title="League rounds",
        yaxis_title="Rating value",
        legend=dict(
            font=dict(
                family='Helvetica',
                size=12,
                color="Black"
            ),
            orientation='h',
            bordercolor="Black",
            borderwidth=2,
            yanchor="bottom",
            xanchor='right',
            x=1,
            y=1
        )
    )
    font_dict = dict(
        family='Helvetica',
        size=26,
        color='black'
    )
    fig.update_layout(
        font=font_dict,  # font formatting
        plot_bgcolor='white',  # background color
    )
    fig.update_yaxes(
        title_text='Rating',  # axis label
        showgrid=False,
        showline=True,
        linecolor='black',  # line color
        linewidth=2.4,  # line size
        tickmode='auto',
        ticklen=10,
        tickfont=dict(
            size=12
        ),
        tickvals=[i for i in range(100, 1501, 100)],
        ticks='inside'
    )
    fig.update_xaxes(
        title_text='Seasons',
        showgrid=False,
        rangemode='tozero',
        showline=True,
        linecolor='black',
        linewidth=2.4,
        tickmode='array',
        ticklen=10,
        tickfont=dict(
            size=14
        ),
        tickvals=[i for i in range(37, 37 * 20, 37)],
        ticktext=[f"Season {int(i / 37)}" for i in range(37, 37 * 20, 37)],
        tickangle=45,
        ticks="inside"
    )
    return fig


def accumulated_betting_chart(
        data_dict
):
    bets = []
    acc_bets = 0
    bet_returns = []
    acc_returns = 0
    bet_expected = []
    acc_expected = 0
    for v in data_dict:
        if v['Season'] > 4:
            for value in ["home", "draw", "away"]:
                bet_value = v[f"bet#{value}"]
                bet_return = v[f"return#bet#{value}"]
                bet_expected_return = v[f"expected#bet#{value}"]
                if bet_value > 0:
                    acc_bets += bet_value
                    acc_returns += bet_return
                    acc_expected += bet_expected_return
                    bets.append(acc_bets)
                    bet_returns.append(acc_returns)
                    bet_expected.append(acc_expected)
    fig = go.Figure()
    for index, (name, trace, line_dash) in enumerate([
        ("Actual returns", bet_returns, 'solid'),
        ("Expected returns", bet_expected, 'dot')
    ]):
        fig.add_trace(
            go.Scatter(
                x=[i for i in range(len(trace))],
                y=trace,
                mode='lines',
                line=dict(
                    color='black',
                    dash=line_dash
                ),
                name=name
            )
        )

    fig.update_layout(
        legend=dict(
            font=dict(
                family='Helvetica',
                size=12,
                color="Black"
            ),
            orientation='h',
            bordercolor="Black",
            borderwidth=2,
            yanchor="bottom",
            xanchor='right',
            x=1,
            y=1
        )
    )
    font_dict = dict(
        family='Helvetica',
        size=22,
        color='black'
    )
    fig.update_layout(
        font=font_dict,  # font formatting
        plot_bgcolor='white',  # background color
    )
    fig.update_yaxes(
        title_text='Accumulated profit',  # axis label
        showgrid=False,
        showline=True,
        zerolinecolor='lightgray',
        linecolor='black',  # line color
        linewidth=2.4,  # line size
        tickmode='auto',
        ticklen=10,
        tickfont=dict(
            size=12
        )
    )
    fig.update_xaxes(
        title_text='Bets in time',
        showgrid=False,
        rangemode='tozero',
        showline=True,
        linecolor='black',
        linewidth=2.4,
        tickmode='auto',
        tickfont=dict(
            size=12
        )
    )

    return fig


def avg_rating_chart(
        network: BaseNetwork,
        ratings_list: [str] = None,
        seasons: [int] = None,
        selected_teams: [int] = None
):
    print(f"Selected teams : {selected_teams}")
    ratings_list = ratings_list or ['true_rating']
    if len(seasons) == 0:
        seasons = range(network.seasons)
    fig = go.Figure()
    selected_teams = selected_teams or []
    if len(selected_teams) > 0:
        for team in selected_teams:
            for rating in ratings_list:
                total, x, y = create_rating_traces(network, team, rating, seasons)
                fig.add_trace(go.Scatter(
                    x=[i for i in range(len(total))],
                    y=total,
                    mode='lines',
                    line=dict(
                        color=px.colors.qualitative.Light24[team],
                        width=3.5
                    ) if rating != 'true_rating' else dict(
                        color=px.colors.qualitative.Light24[team],
                        width=1.5
                    ),
                    name=f"{rating}-Team {team}"
                ))
    else:
        for rating in ratings_list:
            all_teams_total = None
            for team in network.data.nodes:
                total, x, y = create_rating_traces(network, team, rating, seasons)
                if all_teams_total is None:
                    all_teams_total = np.zeros(len(total))
                all_teams_total += total

            fig.add_trace(go.Scatter(
                x=[i for i in range(len(all_teams_total))],
                y=all_teams_total / len(network.data.nodes),
                mode='lines',
                line=dict(
                    width=3.5
                ) if rating != 'true_rating' else dict(
                    width=1.5
                ),
                name=f"{rating}-AVG"
            ))

    fig.update_layout(
        title="Team ratings",
        xaxis_title="League rounds",
        yaxis_title="Rating value",
    )
    return fig


def rating_metrics_chart(
        network: BaseNetwork,
        ratings_list: [str] = None,
        seasons: [int] = None,
        selected_teams: [int] = None
):
    if len(seasons) == 0:
        seasons = range(network.seasons)
    fig = go.Figure()
    selected_teams = selected_teams or []
    if len(selected_teams) > 0:
        for team in selected_teams:
            for rating in ratings_list:
                total, x, y = create_rating_traces(network, team, rating, seasons)
                true_total, x, y = create_rating_traces(network, team, 'true_rating', seasons)
                fig.add_trace(go.Scatter(
                    x=[i for i in range(len(total))],
                    y=np.abs(true_total - total),
                    mode='lines',
                    line=dict(
                        color=px.colors.qualitative.Light24[team],
                        width=3.5
                    ),
                    name=f"{rating}-Team {team}"
                ))
                evaluator = create_rating_evaluation_traces(network, team, rating, seasons)
                fig.add_trace(go.Scatter(
                    x=[i for i in range(len(evaluator))],
                    y=evaluator,
                    mode='lines',
                    line=dict(
                        color=px.colors.qualitative.Light24[team],
                        width=1.5
                    ),
                    name=f"RPS-{rating}-Team {team}"
                ))
    else:
        for rating in ratings_list:
            all_teams_total = None
            all_teams_eval = None
            for team in network.data.nodes:
                total, x, y = create_rating_traces(network, team, rating, seasons)
                true_total, x, y = create_rating_traces(network, team, 'true_rating', seasons)
                total_eval = create_rating_evaluation_traces(network, team, rating, seasons)
                if all_teams_total is None:
                    all_teams_total = np.zeros(len(total))
                    all_teams_eval = np.zeros(len(total_eval))
                all_teams_eval = sum_arrays(all_teams_eval, total_eval)
                all_teams_total = sum_arrays(all_teams_total, np.abs(true_total - total))

            fig.add_trace(go.Scatter(
                x=[i for i in range(len(all_teams_total))],
                y=all_teams_total / len(network.data.nodes),
                mode='lines',
                line=dict(
                    width=3.5
                ),
                name=f"{rating}-ERROR-AVG"
            ))
            fig.add_trace(go.Scatter(
                x=[i for i in range(len(all_teams_eval))],
                y=[a / len(network.data.nodes) for a in all_teams_eval],
                mode='lines',
                line=dict(
                    width=1.5
                ),
                name=f"RPS-{rating}-AVG"
            ))

    fig.update_layout(
        title="Team ratings",
        xaxis_title="League rounds",
        yaxis_title="Rating value",
    )
    return fig


def teams_rating_chart(
        network: BaseNetwork,
        rating: str,
        seasons: [int] = None,
        selected_teams: [int] = None
):
    if len(seasons) == 0:
        seasons = range(network.seasons)
    fig = go.Figure()
    selected_teams = selected_teams or []
    if len(selected_teams) > 0:
        array_ratings = []
        for t_i, team in enumerate(selected_teams):
            total_rating_array = np.array([])
            total_trend_x = np.array([])
            total_trend_y = np.array([])
            for season in seasons:
                rating_array = network.data.nodes[team].get('ratings', {}).get(rating, {}).get(season, [])
                total_rating_array = np.concatenate((total_rating_array, np.array(rating_array)))
                rating_hp = network.data.nodes[team].get('ratings', {}).get("hyper_parameters", {}).get(rating, {}).get(
                    season, {})
                trend_x = np.array(range(len(rating_array)), dtype=np.float) + (len(rating_array) * season)
                total_trend_x = np.concatenate((total_trend_x, trend_x))
                to_zero_trend_x = np.array([i for i in range(len(trend_x))])
                trend_y = to_zero_trend_x * rating_hp.get('trends', [0])[0] * network.days_between_rounds + \
                          rating_hp.get('starting_points', [0])[0]
                total_trend_y = np.concatenate((total_trend_y, trend_y))
            array_ratings.append(total_rating_array)
            fig.add_trace(go.Scatter(
                x=[i for i in range(len(total_rating_array))],
                y=total_rating_array,
                mode='lines',
                line=dict(
                    color=px.colors.sequential.Greys[-((t_i*2) + 1)],
                    width=3
                ),
                name=f"Team {chr(65 + t_i)}"
            ))
        np.save('economic_figure.npy', np.array(array_ratings))
    fig.update_layout(
        xaxis_title="League rounds",
        yaxis_title="Rating value",
        legend=dict(
            font=dict(
                family='Helvetica',
                size=12,
                color="Black"
            ),
            orientation='h',
            bordercolor="Black",
            borderwidth=2,
            yanchor="bottom",
            xanchor='right',
            x=1,
            y=1
        )
    )
    font_dict = dict(
        family='Times New Roman',
        size=20,
        color='black'
    )
    fig.update_layout(
        font=font_dict,  # font formatting
        plot_bgcolor='white',  # background color
    )
    fig.update_yaxes(
        title_text='Rating',  # axis label
        showgrid=False,
        showline=True,
        linecolor='black',  # line color
        linewidth=2.4,  # line size
        tickmode='auto',
        ticklen=10,
        tickfont=dict(
            size=12
        ),
        tickvals=[i for i in range(100, 1501, 100)],
        ticks='inside'
    )
    fig.update_xaxes(
        title_text='Seasons',
        showgrid=False,
        rangemode='tozero',
        showline=True,
        linecolor='black',
        linewidth=2.4,
        tickmode='array',
        ticklen=10,
        tickfont=dict(
            size=14
        ),
        tickvals=[i for i in range(0, 37 * 20, 37)],
        ticktext=[f"Season {int(i / 37)}" for i in range(37, 37 * 20, 37)],
        tickangle=0,
        ticklabelposition="outside right",
        ticks="inside"
    )
    return fig


def create_rating_traces(network, team, rating, seasons):
    total_rating_array = np.array([])
    total_trend_x = np.array([])
    total_trend_y = np.array([])
    for season in seasons:
        rating_array = network.data.nodes[team].get('ratings', {}).get(rating, {}).get(season, [])
        total_rating_array = np.concatenate((total_rating_array, np.array(rating_array)))
        rating_hp = network.data.nodes[team].get('ratings', {}).get("hyper_parameters", {}).get(rating, {}).get(
            season, {})
        trend_x = np.array(range(len(rating_array)), dtype=np.float) + (len(rating_array) * season)
        total_trend_x = np.concatenate((total_trend_x, trend_x))
        to_zero_trend_x = np.array([i for i in range(len(trend_x))])
        trend_y = to_zero_trend_x * rating_hp.get('trends', [0])[0] * network.days_between_rounds + \
                  rating_hp.get('starting_points', [0])[0]
        total_trend_y = np.concatenate((total_trend_y, trend_y))
    return total_rating_array, total_trend_x, total_trend_y


def create_rating_evaluation_traces(network, team, rating, seasons):
    trace = np.array([])
    previous = 1.0
    for away_team, home_team, match_key, match_attributes in network.iterate_over_games():
        if (team in [away_team, home_team]) and (match_attributes['season'] in seasons):
            previous = match_attributes.get('metrics', {rating: previous})[rating]
            trace = np.concatenate((trace, np.array([previous * 100])))
    return trace


def sum_arrays(a, b):
    if len(a) < len(b):
        c = b.copy()
        c[:len(a)] += a
    else:
        c = a.copy()
        c[:len(b)] += b
    return c
