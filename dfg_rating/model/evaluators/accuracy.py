from abc import abstractmethod
from typing import List

from dfg_rating.model.evaluators.base_evaluators import Evaluator


class AccuracyEvaluator(Evaluator):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

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

class RankProbabilityScore(AccuracyEvaluator):

    def _compute(self, observed, model) -> float:
        r = len(self.outcomes)
        score = sum([
            sum([(model[j - 1] - observed[j - 1]) for j in range(1, i + 1)]) ** 2
            for i in range(1, r)
        ])
        score /= (r - 1)
        return score