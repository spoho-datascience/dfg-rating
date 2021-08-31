import pandas as pd
import numpy as np
import datetime
import os
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from tqdm import tqdm
import matplotlib.pyplot as plt
from matplotlib import style
from functools import reduce

pio.templates.default = "plotly_white"
pd.options.display.float_format = '{:.4f}'.format
pd.set_option("display.max_columns", None)

# %%
experiment_df = pd.read_csv(
    os.path.join("experiments", "scripts", "Density_results", "Monday, 09. August 2021 10:30AM.csv"))


# %%

def bootstrap(data, n_iter=9999):
    n = len(data)
    dist_bootstrapped = np.full(shape=n_iter, fill_value=np.nan)
    for i in tqdm(range(n_iter)):
        resample = np.random.choice(data, size=n, replace=True)
        dist_bootstrapped[i] = np.mean(resample)
    quantiles = np.quantile(a=dist_bootstrapped, q=[0.025, 0.975])
    return quantiles[0], quantiles[1]


# %%
in_sample_agg = experiment_df.groupby(['Number_of_nodes', 'Density'], as_index=False).agg({
    'RPS': ['mean', bootstrap]
})
in_sample_agg

# %%

series_data = experiment_df[experiment_df['Number_of_nodes'] == 60]['RPS']
dist = bootstrap(series_data)
#%%
x = in_sample_agg['Density']

y_upper = [t[1] for t in in_sample_agg[('RPS', 'bootstrap')]]
y_lower = [t[0] for t in in_sample_agg[('RPS', 'bootstrap')]]

#%%
fig = go.Figure([
    go.Scatter(
        x=x,
        y=in_sample_agg[('RPS', 'mean')],
        line=dict(color='rgb(0,100,80)'),
        mode='lines'
    ),
    go.Scatter(
        x=pd.concat([x,x[::-1]]), # x, then x reversed
        y=y_upper+y_lower[::-1], # upper, then lower reversed
        fill='toself',
        fillcolor='rgba(0,100,80,0.2)',
        line=dict(color='rgba(255,255,255,0)'),
        hoverinfo="skip",
        showlegend=False
    )
])
fig.update_yaxes(range=[0.1, 0.6])
fig.write_html('fig.html')
