import numpy as np

from dfg_rating.model.forecast.base_forecast import BaseForecast


class LogFunctionForecast(BaseForecast):

    def __init__(self, **kwargs):
        super().__init__('logistic-function', **kwargs)
        self.coefficients = kwargs.get('coefficients')
        self.beta = kwargs.get('beta_parameter', -0.006)
        self.HA = kwargs.get('home_advantage', 50)

    def get_forecast(self, match_data=None, home_team=None, away_team=None, base_ranking='true_rating'):
        # TODO: Add home advantage before diff
        home_rating = home_team.get(
            'ratings', {}
        ).get(
            base_ranking, {}
        ).get(
            match_data['season'], []
        )[match_data['round']]
        away_rating = away_team.get(
            'ratings', {}
        ).get(
            base_ranking, {}
        ).get(
            match_data['season'], []
        )[match_data['round']]
        diff = home_rating - away_rating + self.HA
        for i in range(len(self.outcomes)):
            j = i + 1
            self.probabilities[i] = self.logit_link_function(
                outcome_number=j, covar=diff
            ) - self.logit_link_function(
                outcome_number=j-1, covar=diff
            )
        self.computed = True
        # print(f"Probs {self.probabilities}, sum: {sum(self.probabilities)}")
        return self.probabilities

    def logit_link_function(self, outcome_number, covar):
        if outcome_number == 0:
            return 0
        if outcome_number == len(self.coefficients) + 1:
            return 1
        z = -(self.coefficients[outcome_number - 1]) - (self.beta * covar)
        f = 1 / (1 + np.exp(-z))
        return f

