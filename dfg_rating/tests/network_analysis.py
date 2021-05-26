from dfg_rating.model import factory
from dfg_rating.model.betting.betting import FixedBetting, BaseBetting
from dfg_rating.model.bookmaker.base_bookmaker import BaseBookmaker
from dfg_rating.model.evaluators.accuracy import RankProbabilityScore, Likelihood
from dfg_rating.model.evaluators.profitability import BettingReturnsEvaluator
from dfg_rating.model.forecast.base_forecast import SimpleForecast, BaseForecast
from dfg_rating.model.forecast.true_forecast import LogFunctionForecast
from dfg_rating.model.network.base_network import BaseNetwork

import networkx as nx
import pandas as pd

from dfg_rating.model.network.simple_network import RoundRobinNetwork

pd.set_option('display.max_columns', None)
pd.options.display.width = None
pd.set_option('display.float_format', lambda x: '%.5f' % x)

# %% CREATE NETWORK
network: BaseNetwork = factory.new_network(
    'multiple-round-robin',
    teams=6,
    days_between_rounds=3,
    seasons=4,
    league_teams=6,
    league_promotion=0,
    create=True
)

# %% CUSTOM NETWORK
class CustomNetwork(RoundRobinNetwork):

    def create_data(self):
        if self.data is None:
            graph = nx.MultiDiGraph()
        else:
            graph = self.data



# %% ADD BETTOR AND BOOKMAKER FORECASTS
network.add_forecast(
    forecast=LogFunctionForecast(outcomes=['home', 'draw', 'away'], coefficients=[-1.1, 0.1], beta_parameter=0.006),
    forecast_name='bookmaker_forecast',
    base_ranking='true_rating'
)

network.add_forecast(
    forecast=SimpleForecast(outcomes=['home', 'draw', 'away'], probs=[0.4523, 0.2975, 0.2502]),
    forecast_name='home_forecast',
    base_ranking='true_rating'
)

# %% ADD BOOKMAKER
bookmaker: BaseBookmaker = factory.new_bookmaker(
    'simple',
    error=factory.new_forecast_error(error_type='factor', error=0.0, scope='positive'),
    margin=factory.new_bookmaker_margin('simple', margin=-0.1)
)
network.add_odds(
    bookmaker_name="bm",
    bookmaker=bookmaker,
    base_forecast='bookmaker_forecast'
)

# %% ADD BETTING PLAYER
betting = FixedBetting(1000)
network.add_bets(
    bettor_name='b',
    bookmaker='bm',
    betting=betting,
    base_forecast='home_forecast'
)
#%% LIKELIHOOD
l = Likelihood(
    outcomes=['home', 'draw', 'away'],
    forecast_name='bookmaker_forecast'
)

# %% ACCURACY AND PROFITABILITY EVALUATORS
rps = RankProbabilityScore(
    outcomes=['home', 'draw', 'away'],
    forecast_name="bookmaker_forecast"
)
betting_returns = BettingReturnsEvaluator(
    outcomes=['home', 'draw', 'away'],
    player_name="b",
    player_forecast="home_forecast",
    bookmaker_name="bm"
)

# %% TEST PARAMETERS
p = {
    "network": network,
    "player": ["b"],
    "bookmaker": ["bm"],
    "forecast": ["bookmaker_forecast"]
}
# %% TEST EXECUTION
analysis_dict = []
for away, home, match_id, match_attributes in p['network'].iterate_over_games():
    for f in p['forecast']:
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
        correct, rps_score = rps.eval(match_attributes)
        new_row["ForecastName"] = f
        new_row['RPS'] = rps_score if correct else None
        analysis_dict.append(new_row)
    for o_number, o in enumerate(p['bookmaker']):
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
        match_bets = match_attributes.get('bets', {}).get(p['player'][o_number], [])
        for i_odd, odd in enumerate(match_odds):
            new_row[f"odds#{forecast_object.outcomes[i_odd]}"] = odd
        for i_bet, bet in enumerate(match_bets):
            new_row[f"bet#{forecast_object.outcomes[i_bet]}"] = bet
        new_row['Bettor'] = p['player'][o_number]
        new_row['Bookmaker'] = o
        expected_results, actual_results = betting_returns.eval(match_attributes)
        for i_bet, bet in enumerate(match_bets):
            new_row[f"expected#bet#{forecast_object.outcomes[i_bet]}"] = expected_results[i_bet]
            new_row[f"return#bet#{forecast_object.outcomes[i_bet]}"] = actual_results[i_bet]
        analysis_dict.append(new_row)
# %% TEST RESULTS
print(analysis_dict)

# %%
network.add_evaluation(rps, 'rps')
network.add_evaluation(betting_returns, 'betting_returns')
network.add_evaluation(l, 'logLikelihood')

# %%

network.export(
    forecats=['bookmaker_forecast'],
    metrics=['rps', 'betting_returns', 'logLikelihood'],
    odds=['bm']
)
