import numpy as np
import random


class ForecastError:

    def apply(self, initial_probabilities):
        pass


class ForecastNullError(ForecastError):

    def apply(self, initial_probabilities):
        return initial_probabilities


class ForecastFactorError(ForecastError):

    def __init__(self, error: float, scope: str = None):
        self.type = 'factor'
        self.error = error
        self.scope = scope

    def apply(self, initial_probabilities):
        error_factor = random.uniform(-1.0, 1.0)
        if self.scope == "positive":
            abs_error = abs(error_factor) * self.error
        elif self.scope == "negative":
            abs_error = -1 * abs(error_factor) * self.error
        else:
            abs_error = error_factor * self.error
        applied_probabilities = abs_error + initial_probabilities
        applied_probs = applied_probabilities / sum(applied_probabilities)
        return applied_probs


class ForecastSimulatedError(ForecastError):

    def __init__(self, error: str, **args):
        try:
            self.error_method = getattr(np.random.default_rng(), error)
        except AttributeError:
            print("Error method not available")
            return
        self.error_arguments = args

    def apply(self, initial_probabilities):
        logit_probs = np.log(initial_probabilities / (1 - initial_probabilities))
        self.error_arguments['size'] = len(logit_probs)
        error = self.error_method(**self.error_arguments)
        final_probs = 1 / (1 + (np.exp((-1 * (logit_probs + error)))))
        return final_probs / sum(final_probs)
