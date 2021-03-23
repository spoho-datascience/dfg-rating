from abc import ABC, abstractmethod
from typing import List

from dfg_rating.model import factory
from dfg_rating.model.betting.betting import FixedBetting
from dfg_rating.model.bookmaker.base_bookmaker import BaseBookmaker
from dfg_rating.model.evaluators.accuracy import RankProbabilityScore
from dfg_rating.model.evaluators.profitability import BettingReturnsEvaluator
from dfg_rating.model.forecast.base_forecast import SimpleForecast, BaseForecast
from dfg_rating.model.forecast.true_forecast import LogFunctionForecast
from dfg_rating.model.network.base_network import BaseNetwork

import pandas as pd

pd.set_option('display.max_columns', None)
pd.options.display.width = None
pd.set_option('display.float_format', lambda x: '%.5f' % x)

# %%
network: BaseNetwork = factory.new_network(
    'multiple-round-robin',
    teams=6,
    days_between_rounds=3,
    seasons=4,
    league_teams=6,
    league_promotion=0,
    create=True
)
# %%
network.add_forecast(
    forecast=LogFunctionForecast(outcomes=['home', 'draw', 'away'], coefficients=[0.870, -0.302],
                                 beta_parameter=-0.002),
    forecast_name='param_forecast',
    base_ranking='true_rating'
)

network.add_forecast(
    forecast=SimpleForecast(outcomes=['home', 'draw', 'away'], probs=[0.4523, 0.2975, 0.2502]),
    forecast_name='simple_forecast',
    base_ranking='true_rating'
)

#%%
bookmaker: BaseBookmaker = factory.new_bookmaker(
    'simple',
    error=factory.new_bookmaker_error(error_type='factor', error=0.0, scope='positive'),
    margin=factory.new_bookmaker_margin('simple', margin=-0.1)
)
network.add_odds("simple", bookmaker)
betting = FixedBetting(1000)
network.add_bets(
    "true_bettor",
    "simple",
    betting,
    "true_forecast"
)

# %%

rps = RankProbabilityScore(outcomes=['home', 'draw', 'away'])
rps.eval([1.0, 0.0, 0.0], observed_result='home')
print(rps.eval([0.80, 0.10, 0.10], observed_result='home'))

# %%
betting_returns = BettingReturnsEvaluator(outcomes=['home', 'draw', 'away'])
expected, actual = betting_returns.eval(
    bets=[10, 10, 10],
    bettor_predictions=[0.305766501196908, 0.288109830070559, 0.406123668732533],
    bookmaker_odds=[3.59751639141012, 3.81798843771005, 2.70853457872322],
    observed_result='away'
)
print(expected, actual)

# %%
analysis_dict = []
#forecasts = ['true_forecast', 'param_forecast']
forecasts = []
odds = ["simple"]
bets = ["true_bettor"]
for away, home, match_id, match_attributes in network.iterate_over_games():
    for f in forecasts:
        new_row = {
            "HomeTeam": home,
            "AwayTeam": away,
            "Season": match_attributes.get('season', None),
            "Round": match_attributes.get('season', None),
            "Result": match_attributes.get('winner', None),
        }
        forecast_object: BaseForecast = match_attributes.get('forecasts', {}).get(f, None)
        if forecast_object is not None:
            for i, outcome in enumerate(forecast_object.outcomes):
                new_row[outcome] = forecast_object.probabilities[i]
        correct, rps_score = rps.eval(forecast_object.probabilities, observed_result=match_attributes.get('winner'))
        new_row["ForecastName"] = f
        new_row['RPS'] = rps_score if correct else None
        analysis_dict.append(new_row)
    for o_number, o in enumerate(odds):
        print(match_attributes)
        new_row = {
            "HomeTeam": home,
            "AwayTeam": away,
            "Season": match_attributes.get('season', None),
            "Round": match_attributes.get('season', None),
            "Result": match_attributes.get('winner', None),
        }
        forecast_object: BaseForecast = match_attributes.get('forecasts', {}).get('true_forecast', None)
        if forecast_object is not None:
            for i, outcome in enumerate(forecast_object.outcomes):
                new_row[outcome] = forecast_object.probabilities[i]
        match_odds = match_attributes.get('odds', {}).get(o, [])
        match_bets = match_attributes.get('bets', {}).get(bets[o_number], [])
        print(match_odds, match_bets)
        for i_odd, odd in enumerate(match_odds):
            new_row[f"odds#{forecast_object.outcomes[i_odd]}"] = odd
        for i_bet, bet in enumerate(match_bets):
            new_row[f"bet#{forecast_object.outcomes[i_bet]}"] = bet
        new_row['Bettor'] = bets[o_number]
        new_row['Bookmaker'] = o
        expected_results, actual_results = betting_returns.eval(
            bets=match_bets,
            bettor_predictions=forecast_object.probabilities,
            bookmaker_odds=match_odds,
            observed_result=new_row['Result']
        )
        for i_bet, bet in enumerate(match_bets):
            new_row[f"expected#bet#{forecast_object.outcomes[i_bet]}"] = expected_results[i_bet]
            new_row[f"return#bet#{forecast_object.outcomes[i_bet]}"] = actual_results[i_bet]
        analysis_dict.append(new_row)
# %%
df = pd.DataFrame(analysis_dict)
df.set_index(['HomeTeam', 'AwayTeam', 'Season', 'Round'], inplace=True)
df.to_csv('table.csv')
