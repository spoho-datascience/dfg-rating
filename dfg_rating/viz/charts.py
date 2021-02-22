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
        reduced_color_scale: List[str] = px.colors.qualitative.Light24,
        show_trend = False,
        selected_teams =  []
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
    for team in selected_teams:
        for rating in ratings:
            total_rating_array = np.array([])
            total_trend_x = np.array([])
            total_trend_y = np.array([])
            rating_name = "Logistic Rating" if rating == 'true_rating' else "Ranking"
            for season in range(network.seasons):
                rating_array = network.data.nodes[team].get('ratings', {}).get(rating, {}).get(season, [])
                total_rating_array = np.concatenate((total_rating_array, np.array(rating_array)))
                rating_hp = network.data.nodes[team].get('ratings', {}).get("hyper_parameters", {}).get(rating, {}).get(
                    season, {})
                trend_x = np.array(range(len(rating_array)), dtype=np.float) + (len(rating_array) * season)
                total_trend_x = np.concatenate((total_trend_x, trend_x))
                trend_y = trend_x * rating_hp.get('trends', [0])[0] * network.days_between_rounds + \
                          rating_hp.get('starting_points', [0])[0]
                total_trend_y = np.concatenate((total_trend_y, trend_y))

            fig.add_trace(go.Scatter(
                x=[i for i in range(len(total_rating_array))],
                y=total_rating_array,
                mode='lines+markers',
                line=dict(color=reduced_color_scale[team]),
                name=f"{rating_name}-Team {team}"
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
                    name=f"{rating_name}-Trend team {team}"
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
        show_trend=True,
        teams: [int] = [2]
) -> go.Figure:
    fig = go.Figure()
    for team in teams:
        for rating in ratings:
            total_rating_array = np.array([])
            total_trend_x = np.array([])
            total_trend_y = np.array([])
            for season in range(network.seasons):
                rating_array = network.data.nodes[team].get('ratings', {}).get(rating, {}).get(season, [])
                total_rating_array = np.concatenate((total_rating_array, np.array(rating_array)))
                rating_hp = network.data.nodes[team].get('ratings', {}).get("hyper_parameters", {}).get(rating, {}).get(
                    season, {})
                trend_x = np.array(range(len(rating_array)), dtype=np.float) + (len(rating_array) * season)
                total_trend_x = np.concatenate((total_trend_x, trend_x))
                trend_y = trend_x * rating_hp.get('trends', [0])[0] * network.days_between_rounds + \
                          rating_hp.get('starting_points', [0])[0]
                total_trend_y = np.concatenate((total_trend_y, trend_y))

            fig.add_trace(go.Scatter(
                x=[i for i in range(len(total_rating_array))],
                y=total_rating_array,
                mode='lines',
                line=dict(color='black'),
                name='Team rating'
            ))
            fig.add_trace(go.Scatter(
                x=[0],
                y=[network.data.nodes[team].get('ratings', {}).get("hyper_parameters", {}).get(rating, {}).get(
                    0, {}).get('starting_points', [0])[0]],
                mode='markers',
                marker=dict(color='black', size=12),
                name="Starting point"
            ))
            if show_trend:
                fig.add_trace(go.Scatter(
                    x=total_trend_x,
                    y=total_trend_y,
                    mode='lines',
                    line=dict(
                        width=0.5,
                        color="black",
                        dash='dash'
                    ),
                    name='Trend'
                ))
    fig.update_layout(
        xaxis_title="League rounds",
        yaxis_title="Rating value",
    )
    font_dict = dict(family='Helvetica',
                   size=26,
                   color='black'
                   )
    fig.update_layout(
        font=font_dict,  # font formatting
        plot_bgcolor='white',  # background color
    )
    fig.update_yaxes(title_text='Rating',  # axis label
                     showgrid=False,
                     showline=True,
                     showticklabels=False, # add line at x=0
                     linecolor='black',  # line color
                     linewidth=2.4, # line size
                     )
    fig.update_xaxes(title_text='Time',
                     showgrid=False,
                     rangemode='tozero',
                 showline=True,
                 showticklabels=False,
                 linecolor='black',
                 linewidth=2.4,
                     range=[0,38]
                 )
    return fig
