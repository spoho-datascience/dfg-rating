import plotly.graph_objects as go

from dfg_rating.model.network.base_network import BaseNetwork


def create_ratings_charts(network: BaseNetwork, rating='true_rating'):
    fig = go.Figure()
    for team in network.data.nodes:
        rating_array = network.data.nodes[team].get('ratings', {}).get(rating, {})[-1]
        print(rating_array)
        fig.add_trace(go.Scatter(
            x=[i for i in range(len(rating_array))],
            y=rating_array,
            mode='lines+markers',
            name=team
        ))
    return fig
