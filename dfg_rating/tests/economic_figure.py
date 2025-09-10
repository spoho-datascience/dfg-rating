from typing import List

import plotly.graph_objects as go
import plotly.express as px
import numpy as np



fig = go.Figure()
array_ratings = np.load('economic_figure.npy')
for t_i, total_rating_array in enumerate(array_ratings):
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
config = {
    'toImageButtonOptions': {
        'format': 'svg', # one of png, svg, jpeg, webp
        'filename': 'teams_rating_economic_paper',
        'scale': 1 # Multiply title/legend/axis/canvas sizes by this factor
    }
}
fig.show(config=config)