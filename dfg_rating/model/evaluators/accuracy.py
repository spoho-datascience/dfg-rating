from abc import abstractmethod
from typing import List
import numpy as np

from dfg_rating.model.evaluators.base_evaluators import Evaluator


class AccuracyEvaluator(Evaluator):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.forecast_name = kwargs.get('forecast_name')

    def eval(self, match_attributes):
        probabilities: List[float] = match_attributes['forecasts'][self.forecast_name].probabilities
        observed_result = match_attributes['winner']
        if len(probabilities) != len(self.outcomes):
            return 0, "Probabilities do not fit in potential outcomes array"
        observed_probabilities = [1.0 if observed_result == outcome else 0.0 for outcome in self.outcomes]
        evaluation_score = self._compute(observed=observed_probabilities, model=probabilities)
        return 1, evaluation_score

    @abstractmethod
    def _compute(self, observed, model) -> float:
        """Numerical evaluation of a forecast given the probabilities set
        """
        pass


class RankProbabilityScore(AccuracyEvaluator):

    def _compute(self, observed, model) -> float:
        r = len(self.outcomes)
        score = sum([
            sum([(model[j - 1] - observed[j - 1]) for j in range(1, i + 1)]) ** 2
            for i in range(1, r)
        ])
        score /= (r - 1)
        return score


class ExpectedRankProbabilityScore(RankProbabilityScore):

    def eval(self, match_attributes):
        probabilities: List[float] = match_attributes['forecasts'][self.forecast_name].probabilities
        true_probabilities: List[float] = match_attributes['forecasts']["true_forecast"].probabilities
        if len(probabilities) != len(self.outcomes):
            return 0, "Probabilities do not fit in potential outcomes array"
        evaluation_score = 0.0
        for i in range(len(self.outcomes)):
            observed_model = [0.0 for outcome in self.outcomes]
            observed_model[i] = 1.0
            evaluation_score += true_probabilities[i] * self._compute(observed=observed_model, model=probabilities)
        return 1, evaluation_score


class ForecastError(RankProbabilityScore):

    def eval(self, match_attributes):
        probabilities: List[float] = match_attributes['forecasts'][self.forecast_name].probabilities
        true_probabilities: List[float] = match_attributes['forecasts']["true_forecast"].probabilities
        if len(probabilities) != len(self.outcomes):
            return 0, "Probabilities do not fit in potential outcomes array"
        evaluation_score = self._compute(observed=true_probabilities, model=probabilities)
        return 1, evaluation_score


class ProbabilityDifference(AccuracyEvaluator):

    def _compute(self, observed, model) -> float:
        return model[0] - model[-1]


class ProbabilityPointer(AccuracyEvaluator):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.probability_pointer = kwargs.get('probability_index', 0)

    def _compute(self, observed, model) -> float:
        return model[self.probability_pointer]


class FavouriteProbability(AccuracyEvaluator):

    def _compute(self, observed, model) -> float:
        return max(model[0], model[-1])


class Likelihood(AccuracyEvaluator):

    def _compute(self, observed, model) -> float:
        score = sum([
            np.log(m * o)
            for m, o in zip(model, observed) if o > 0
        ])
        return score
