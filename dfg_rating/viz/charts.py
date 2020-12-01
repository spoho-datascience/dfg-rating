import plotly.graph_objects as go
import plotly.express as px
import numpy as np

from dfg_rating.model.network.base_network import BaseNetwork


def create_ratings_charts(network: BaseNetwork, rating='true_rating', colorscale=px.colors.qualitative.Light24):
    fig = go.Figure()
    reduced_colorscale = np.random.choice(colorscale, network.n_teams)
    for team in network.data.nodes:
        total_rating_array = np.array([])
        total_trend_x = np.array([])
        total_trend_y = np.array([])
        print(f"Team{team}: ", network.data.nodes[team])
        for season in range(network.seasons):
            print(f"Season {season}")
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
            line=dict(color=reduced_colorscale[team]),
            name=f"Team {team}"
        ))
        fig.add_trace(go.Scatter(
            x=total_trend_x,
            y=total_trend_y,
            mode='lines',
            line=dict(
                width=0.5,
                color=reduced_colorscale[team],
            ),
            name=f"Trend team {team}"
        ))
    return fig
