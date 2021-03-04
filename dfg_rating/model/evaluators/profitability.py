from abc import abstractmethod
from typing import List

from dfg_rating.model.evaluators.base_evaluators import Evaluator


class ProfitabilityEvaluator(Evaluator):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.outcomes = kwargs.get("outcomes")

    @abstractmethod
    def eval(self, bets: List[float], bettor_predictions: List[float], bookmaker_odds: List[float],
             observed_result: str) -> (float, str):
        pass


class BettingReturnsEvaluator(ProfitabilityEvaluator):

    def eval(self, bets: List[float], bettor_predictions: List[float], bookmaker_odds: List[float],
             observed_result: str) -> (float, str):
        expected_returns = []
        actual_returns = []
        for bet_index, bet in enumerate(bets):
            expected_returns.append((bettor_predictions[bet_index] * bookmaker_odds[bet_index]) - 1)
            bet_result = 1 if self.outcomes[bet_index] == observed_result else 0
            actual_returns.append((bet_result * bookmaker_odds[bet_index]) - 1)
        return expected_returns, actual_returns
