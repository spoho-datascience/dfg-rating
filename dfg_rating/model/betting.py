import numpy as np
from abc import ABC, abstractmethod

from dfg_rating.model.forecast.base_forecast import BaseForecast


class BaseBetting(ABC):

    @abstractmethod
    def bet(self, forecast: BaseForecast, odds):
        pass


class FixedBetting(BaseBetting):

    def __init__(self, bank_role: int):
        self.bank_role = bank_role

    def bet(self, forecast: BaseForecast, odds):
        print(forecast.get_forecast())
        betting_inputs = forecast.get_forecast() * odds

        def decide_betting(i):
            return 0.01 * self.bank_role if i > 1 else 0.0

        bets = np.array([decide_betting(i) for i in betting_inputs])
        return bets
