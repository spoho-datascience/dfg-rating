"""Module of helpers building charts and data visualizations
"""
from typing import List

import plotly.graph_objects as go
import plotly.express as px
import numpy as np

from dfg_rating.model.network.base_network import BaseNetwork


def create_ratings_charts(
        network: BaseNetwork, rating: str = 'true_rating', color_scale: List[str] = px.colors.qualitative.Light24
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
    reduced_color_scale = np.random.choice(color_scale, network.get_number_of_teams())
    for team in network.data.nodes:
        total_rating_array = np.array([])
        total_trend_x = np.array([])
        total_trend_y = np.array([])
        print(f"Team{team}: ", network.data.nodes[team])
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
            name=f"Team {team}"
        ))
        fig.add_trace(go.Scatter(
            x=total_trend_x,
            y=total_trend_y,
            mode='lines',
            line=dict(
                width=0.5,
                color=reduced_color_scale[team],
            ),
            name=f"Trend team {team}"
        ))
    return fig
