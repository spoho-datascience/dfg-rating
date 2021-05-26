from abc import abstractmethod
from typing import List

from dfg_rating.model.evaluators.base_evaluators import Evaluator


class ProfitabilityEvaluator(Evaluator):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.outcomes = kwargs.get("outcomes")
        self.player_name = kwargs.get("player_name")
        self.true_model = kwargs.get("true_model")
        self.bookmaker_name = kwargs.get("bookmaker_name")

    @abstractmethod
    def eval(self, match_attributes):
        pass


class BettingReturnsEvaluator(ProfitabilityEvaluator):

    def eval(self, match_attributes):
        ## Should be using the true model forecast for evaluation
        bets: List[float] = match_attributes['bets'][self.player_name]
        # bettor_predictions: List[float] = match_attributes['forecasts'][self.player_forecast].probabilities
        true_model: List[float] = match_attributes['forecasts'][self.true_model].probabilities
        bookmaker_odds: List[float] = match_attributes['odds'][self.bookmaker_name]
        observed_result = match_attributes.get('winner')
        expected_returns = []
        actual_returns = []
        for bet_index, bet in enumerate(bets):
            expected_returns.append(bet * ((true_model[bet_index] * bookmaker_odds[bet_index]) - 1))
            bet_result = 1.0 if self.outcomes[bet_index] == observed_result else 0.0
            actual_returns.append(bet * ((bet_result * bookmaker_odds[bet_index]) - 1))
        return 1, [(a, e) for a, e in zip(actual_returns, expected_returns)]
