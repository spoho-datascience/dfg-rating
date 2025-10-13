import os
import glob
import pandas as pd
import numpy as np

import dfg_rating.viz.jupyter_widgets as Widgets
import dfg_rating.viz.tables as DFGTables
from dfg_rating.model.network.base_network import WhiteNetwork
from dfg_rating.model.rating.elo_rating import ELORating, GoalsELORating, OddsELORating

from dfg_rating.model.forecast.true_forecast import LogFunctionForecast
from dfg_rating.model.forecast.base_forecast import SimpleForecast
from dfg_rating.model.evaluators.accuracy import RankProbabilityScore, Likelihood

# set parameters
# use Elo odds or Elo goals for rating calculation
rating = 'ELO odds'  # 'ELO goals'
# If true, adjust each teams rating of the respective leagues, when inter-league match occurred
league_average = True  # False
# If true, use a different parameter for inter-league matches
param_adjust = True  # False
data_path = os.path.join("../..", "data", "real", "league_comparability", "all_data_filtered_new.xlsx")

all_data = pd.read_excel(data_path)
print("Data loaded")

# Convert the 'date' column to datetime format
all_data['date'] = pd.to_datetime(all_data['date'], format='%d.%m.%Y %H:%M')
all_data = all_data.sort_values(by='date')


# Function to assign round numbers within each season
def assign_rounds(df):
    # Extract only the date part (ignoring time)
    df['match_day'] = df['date'].dt.date

    # Get unique match days for the season and assign consecutive round numbers
    unique_days = df['match_day'].unique()
    round_mapping = {day: round_num for round_num, day in enumerate(unique_days)}

    # Map the round numbers back to the DataFrame
    df['round'] = df['match_day'].map(round_mapping)

    return df


# Apply the round assignment function to each season
all_data = all_data.groupby('season_id').apply(assign_rounds)

# Drop the intermediate 'match_day' column if not needed
all_data.drop(columns=['match_day'], inplace=True)

# Reset the index after groupby
all_data.reset_index(drop=True, inplace=True)

# get training data set (first three seasons)
training_data = all_data[all_data['season_id'].isin([0, 1, 2])]

training_data_network = WhiteNetwork(
    data=training_data,
    mapping={
        "node2": {
            "id": "home_team_id",
            "name": "home_team",
        },
        "node1": {
            "id": "away_team_id",
            "name": "away_team",
        },
        "day": "date",
        "dayIsTimestamp": True,
        "ts_format": "%d.%m.%Y %H:%M",
        "season": "season_id",
        "winner": {
            "result": "result",
            "translation": {
                "home": "home",
                "draw": "draw",
                "away": "away"
            }
        },
        "round": "round",
        "home_score": "home_score",
        "away_score": "away_score",
        "odds": {
            "average_odds": {
                "home": "home_odds_new",
                "draw": "draw_odds_new",
                "away": "away_odds_new"
            }
        },

    },
    days_between_rounds=3
)

if rating == 'ELO odds':
    for k in range(50, 401, 25):
        print('k')
        # elo = ELORating(trained=False, param_k=k)
        # real_data_network.add_rating(rating=elo, rating_name="test_elo_rating")
elif rating == 'ELO goals':
    for k0 in range(2, 11, 2):
        for l in [0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0]:
            print('l')
            # elo = ELORating(trained=False, param_k=20)
            # real_data_network.add_rating(rating=elo, rating_name="test_elo_rating")

training_data_network.export(filename='test.csv')

elo = ELORating(trained=True, param_k=20, rating_name="test_elo_rating")
training_data_network.add_rating(rating=elo, rating_name="test_elo_rating")
training_data_network.add_forecast(
    forecast=LogFunctionForecast(outcomes=['home', 'draw', 'away'], coefficients=[-1.1, 0.1], beta_parameter=0.006),
    forecast_name='base_forecast',
    base_ranking='test_elo_rating'
)

training_data_network.add_rating(
    rating=GoalsELORating(trained=True, param_k=4, param_lam=1.6, rating_name="test_goals_elo_rating"),
    rating_name="test_goals_elo_rating"
)

training_data_network.add_rating(
    rating=OddsELORating(
        trained=True, 
        param_k=175,
        home_odds_pointer="home_odds_new",
        draw_odds_pointer="draw_odds_new",
        away_odds_pointer="away_odds_new",
        rating_name="test_odds_elo_rating"
    ),
    rating_name="test_odds_elo_rating"
)

training_data_network.export(ratings=['test_elo_rating', 'test_goals_elo_rating', 'test_odds_elo_rating'])

app = Widgets.RatingsExplorer(network=training_data_network)
app.run('external', port=8001)
