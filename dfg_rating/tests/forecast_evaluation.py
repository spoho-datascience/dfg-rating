from abc import ABC, abstractmethod
from typing import List

from dfg_rating.model import factory
from dfg_rating.model.betting.betting import FixedBetting
from dfg_rating.model.bookmaker.base_bookmaker import BaseBookmaker
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
    margin=factory.new_bookmaker_margin('simple', margin=0.1)
)
network.add_odds("simple", bookmaker)
betting = FixedBetting(1000)
network.add_bets(
    "param_forecast_bettor",
    "simple",
    betting,
    "param_forecast"
)

# %%
class ForecastEvaluator(ABC):

    def __init__(self, **kwargs):
        self.outcomes = kwargs.get("outcomes")

    @abstractmethod
    def eval(self, probabilities: List[float], observed_result: str) -> (float, str):
        """Evaluate specific probabilities from a forecast model
        """
        pass


class AccuracyForecastEvaluator(ForecastEvaluator):

    def eval(self, probabilities: List[float], observed_result: str) -> (float, str):
        if len(probabilities) != len(self.outcomes):
            return 0, "Probabilities do not fit in potential outcomes array"
        observed_probabilities = [1.0 if observed_result == outcome else 0.0 for outcome in self.outcomes]
        print(observed_probabilities)
        evaluation_score = self._compute(observed=observed_probabilities, model=probabilities)
        return 1, evaluation_score

    @abstractmethod
    def _compute(self, observed, model) -> float:
        """Numerical evaluation of a forecast given the probabilities set
        """
        pass


class RankProbabilityScore(AccuracyForecastEvaluator):

    def _compute(self, observed, model) -> float:
        r = len(self.outcomes)
        score = sum([
            sum([(model[j - 1] - observed[j - 1]) for j in range(1, i + 1)]) ** 2
            for i in range(1, r)
        ])
        score /= (r - 1)
        return score

#%%

class ProfitabilityForecastEvaluator(ForecastEvaluator, ABC):
    pass


class BettingReturnsEvaluator(ProfitabilityForecastEvaluator):

    def eval(self, probabilities: List[float], observed_result: str) -> (float, str):
        pass


# %%

rps = RankProbabilityScore(outcomes=['home', 'draw', 'away'])
rps.eval([1.0, 0.0, 0.0], observed_result='home')
rps.eval([0.80, 0.10, 0.10], observed_result='home')

# %%
analysis_dict = []
forecasts = ['true_forecast', 'param_forecast']
for away, home, match_id, match_attributes in network.iterate_over_games():
    for f in forecasts:
        print(match_attributes['odds']['simple'])
        print(match_attributes['bets']['param_forecast_bettor'])
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
# %%
df = pd.DataFrame(analysis_dict)
df.set_index(['HomeTeam', 'AwayTeam', 'Season', 'Round'], inplace=True)
df.head(30).to_csv('table.csv')
