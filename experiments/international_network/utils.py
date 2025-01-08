import os
import glob
import pandas as pd
import numpy as np
import re
from dfg_rating.model.network.base_network import WhiteNetwork, BaseNetwork
import statsmodels.api as sm
from statsmodels.miscmodels.ordinal_model import OrderedModel
from skopt import gp_minimize
from scipy.optimize import minimize
import statistics as sc


def read_excel_data(folder_path):
    # List all Excel files in the folder
    excel_files = [f for f in glob.glob(os.path.join(folder_path, '*.xlsx')) if not os.path.basename(f).startswith('~$')]

    # Initialize an empty list to store DataFrames
    dfs = []

    # Read each Excel file into a DataFrame
    for file in excel_files:
        df = pd.read_excel(file)
        dfs.append(df)
        print(f'Read {file}')

    # Concatenate all DataFrames into a single DataFrame
    all_data = pd.concat(dfs, ignore_index=True)

    return all_data


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


def get_teams_per_season(df, team_id_map):
    network_info = {}
    team_ids = {}
    key_counter = 0
    # Iterate through each season
    for season, group in df.groupby('Season'):
        # Get all unique teams from home and away columns
        teams = pd.unique(group[['Home', 'Away']].values.ravel('K'))

        # Map team names to their corresponding IDs using the team_id_mapping dictionary
        for team in teams:
            if team in team_id_map:
                # Assign a consecutive number as key, and the team ID as value
                team_ids[key_counter] = team_id_map[team]
                key_counter += 1

        # Store the team IDs under the correct season in the "teams_playing" field
        network_info[str(season)] = {"teams_playing": team_ids}

    return network_info


def setup_network(training_data, network_info_dict):
    network = WhiteNetwork(
        data=training_data,
        network_info=network_info_dict,
        mapping={
            "node2": {
                "id": "home_team_id",
                "name": "Home",
                "ratings": {"true_rating": "true_rating#Home",
                            "ranking": "ranking#Home"},
                #"league_id": 'home_team_league_id',
            },
            "node1": {
                "id": "away_team_id",
                "name": "Away",
                "ratings": {"true_rating": "true_rating#Away",
                            "ranking": "ranking#Away"},
                #"league_id": 'away_team_league_id',
            },
            "day": "Day",
            "dayIsTimestamp": False,
            "ts_format": "%d.%m.%Y %H:%M",
            "season": "Season",
            "winner": {
                "result": "Result",
                "translation": {
                    "home": "home",
                    "draw": "draw",
                    "away": "away"
                }
            },
            "round": "Round",
            "home_score": "home_score",
            "away_score": "away_score",
            #"odds": {
            #    "average_odds": {
            #        "home": "home_odds_new",
            #        "draw": "draw_odds_new",
            #        "away": "away_odds_new"
            #    }
            #},

        },
    )
    return network


def get_ratings_of_match(r, data_network, training_seasons):
    network_flat = []
    home_rating = []
    away_rating = []
    outcome = []
    for away_team, home_team, edge_key, edge_attributes in data_network.data.edges(keys=True, data=True):
        if edge_attributes.get('Season') in training_seasons:
            match_dict = {
                "Home": home_team,
                "Home_team": edge_attributes.get('Home', 0),
                "Away": away_team,
                "Away_team": edge_attributes.get('Away', 0),
                "Season": edge_attributes.get('season', 0),
                "Round": edge_attributes.get('round', -1),
                "Day": edge_attributes.get('day', -1),
                "Result": edge_attributes.get('winner', 'none'),
            }
            for team, name in [(home_team, 'Home'), (away_team, 'Away')]:
                rating_dict = data_network.data.nodes[team].get('ratings', {}).get(r)
                # rating_dict = rating_dict[rating_dict['season_id'].isin(training_seasons)]
                match_dict[f"{r}#{name}"] = rating_dict.get(edge_attributes.get('Season', 0))[
                    data_network.round_values.index(edge_attributes.get('Round', 0))]
                if name == 'Home':
                    home_rating.append(rating_dict.get(edge_attributes.get('Season', 0))[
                                           data_network.round_values.index(edge_attributes.get('Round', 0))])
                    out = match_dict.get('Result')
                    if out == 'home':
                        outcome.append(2)
                    elif out == 'draw':
                        outcome.append(1)
                    elif out == 'away':
                        outcome.append(0)
                elif name == 'Away':
                    away_rating.append(rating_dict.get(edge_attributes.get('Season', 0))[
                                           data_network.round_values.index(edge_attributes.get('Round', 0))])
            network_flat.append(match_dict)
    return network_flat, home_rating, away_rating, outcome


def log_coefficients(rating_diffs, outcomes):
    # Add a constant (intercept) to the model
    x = sm.add_constant(rating_diffs)
    # Fit ordered logistic regression model
    model = OrderedModel(outcomes, rating_diffs, distr='logit')
    reg = model.fit()
    # Extract coefficients and beta
    print(reg.params)
    coeffs = reg.params
    return coeffs


def get_log_coeffs(training_seasons, data_network, r):
    data, home_rating, away_rating, outcomes = get_ratings_of_match(r, data_network, training_seasons)
    rat_diff = []
    if len(home_rating) == len(away_rating):
        rat_diff = [home - away for home, away in zip(home_rating, away_rating)]
    rating_diffs = np.array([rat_diff])  # Covariate (rating differences)
    outcomes = np.array([outcomes])  # 0: away win, 1: draw, 2: home win
    outcomes = outcomes.flatten()
    rating_diffs = rating_diffs.reshape(-1, 1)
    coeff = log_coefficients(rating_diffs, outcomes)
    return coeff


def get_rps(data_network, seasons):
    rps = []
    for away_team, home_team, edge_key, edge_attributes in data_network.data.edges(keys=True, data=True):
        if edge_attributes.get('Season') in seasons:
            #if edge_attributes.get('competition') in ['International', 'Cup']:
            rps.append(edge_attributes.get('metrics', {}).get('rps', -1))
    mean_rps = sc.fmean(rps)
    return mean_rps


def get_llh(data_network, seasons):
    llh = []
    for away_team, home_team, edge_key, edge_attributes in data_network.data.edges(keys=True, data=True):
        if edge_attributes.get('Season') in seasons:
            llh.append(edge_attributes.get('metrics', {}).get('llh', -1))
    mean_llh = sc.fmean(llh)
    return mean_llh
