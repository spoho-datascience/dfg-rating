import json

from dfg_rating.db.postgres import PostgreSQLDriver
from dfg_rating.logic.controller import Controller
from dfg_rating.model import factory
from dfg_rating.model.betting.betting import FixedBetting
from dfg_rating.model.bookmaker.base_bookmaker import BaseBookmaker
from dfg_rating.model.evaluators.accuracy import RankProbabilityScore
from dfg_rating.model.evaluators.profitability import BettingReturnsEvaluator
from dfg_rating.model.forecast.base_forecast import SimpleForecast
from dfg_rating.model.network.base_network import BaseNetwork

test_network: BaseNetwork = factory.new_network('round-robin', teams=20, days_between_rounds=3)
test_network.add_forecast(
    forecast=SimpleForecast(outcomes=['home', 'draw', 'away'], probs=[0.4523, 0.2975, 0.2502]),
    forecast_name='simple_forecast',
    base_ranking='true_rating'
)
bookmaker: BaseBookmaker = factory.new_bookmaker(
    'simple',
    error=factory.new_forecast_error(error_type='factor', error=0.0, scope='positive'),
    margin=factory.new_bookmaker_margin('simple', margin=-0.1)
)
test_network.add_odds("simple", bookmaker, "true_forecast")
betting = FixedBetting(1000)
test_network.add_bets(
    "true_bettor",
    "simple",
    betting,
    "simple_forecast"
)
rps = RankProbabilityScore(outcomes=['home', 'draw', 'away'], forecast_name="simple_forecast")
betting_returns = BettingReturnsEvaluator(
    outcomes=['home', 'draw', 'away'], bookmaker_name="simple", player_name="true_bettor", true_model="true_forecast"
)
test_network.add_evaluation(
    evaluators_list=[(rps, "RPS_simple"), (betting_returns, "betting_returns_simple")]
)
network_serialized = test_network.serialize_network("test_network")

all_matches = [(a,h,m_id,attributes) for a,h,m_id,attributes in test_network.iterate_over_games() if (a == 0)]

print(all_matches)

mc = Controller()
mc.networks["test_network"] = test_network
mc.save_network("test_network")

