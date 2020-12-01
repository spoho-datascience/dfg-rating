import numpy as np

from dfg_rating.model.forecast.base_forecast import BaseForecast


class LogFunctionForecast(BaseForecast):

    def __init__(self, **kwargs):
        super().__init__('logistic-function', **kwargs)
        self.coefficients = kwargs.get('coefficients')
        self.beta = kwargs.get('beta_parameter', 0.003)

    def get_forecast(self, match_data=None, home_team=None, away_team=None):
        home_rating = home_team.get(
            'ratings', {}
        ).get(
            'true_rating', {}
        ).get(
            match_data['season'], []
        )[match_data['round']]
        away_rating = away_team.get(
            'ratings', {}
        ).get(
            'true_rating', {}
        ).get(
            match_data['season'], []
        )[match_data['round']]
        diff = home_rating - away_rating
        for i in range(len(self.outcomes)):
            self.probabilities[i] = self.logit_link_function(
                outcome_number=i, covar=diff
            ) - self.logit_link_function(
                outcome_number=i-1, covar=diff
            )
        return self.probabilities

    def logit_link_function(self, outcome_number, covar):
        if outcome_number < 0:
            return 1
        if outcome_number >= len(self.coefficients):
            return 0
        z = -(self.coefficients[outcome_number]) - (self.beta * covar)
        return 1 / (1 + np.exp(-z))
