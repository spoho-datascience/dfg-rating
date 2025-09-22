import numpy as np


class ForecastError:

    def apply(self, initial_probabilities):
        pass


class ForecastNullError(ForecastError):

    def apply(self, initial_probabilities):
        return initial_probabilities


class ForecastFactorError(ForecastError):

    def __init__(self, error: float, scope: str = None, random_number_generator = np.random.default_rng(),):
        self.type = 'factor'
        self.error = error
        self.scope = scope
        self.random_number_generator = random_number_generator

    def apply(self, initial_probabilities):
        error_factor = self.random_number_generator.uniform(-1.0, 1.0)
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

    def __init__(self, error: str, random_number_generator = np.random.default_rng(), **args):
        self.random_number_generator = random_number_generator
        try:
            self.error_method = getattr(self.random_number_generator, error)
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
