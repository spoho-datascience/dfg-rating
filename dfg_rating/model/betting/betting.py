import numpy as np
from abc import ABC, abstractmethod

from dfg_rating.model.forecast.forecast_error import ForecastError, NullError


class BaseBetting(ABC):

    def __init__(self, error: ForecastError = None):
        self.error = error if error is not None else NullError()

    @abstractmethod
    def bet(self, forecast, odds):
        pass


class FixedBetting(BaseBetting):

    def __init__(self, bank_role: int, error: ForecastError = None):
        super().__init__(error)
        self.bank_role = bank_role

    def bet(self, forecast, odds):
        forecast_with_error = self.error.apply(forecast)
        betting_inputs = [f * o for f, o in zip(forecast_with_error, odds)]

        def decide_betting(i):
            return 0.01 * self.bank_role if i > 1.0 else 0.0

        bets = np.array([decide_betting(i) for i in betting_inputs])
        return bets
