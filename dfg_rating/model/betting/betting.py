import numpy as np
from abc import ABC, abstractmethod



class BaseBetting(ABC):

    @abstractmethod
    def bet(self, forecast, odds):
        pass


class FixedBetting(BaseBetting):

    def __init__(self, bank_role: int):
        self.bank_role = bank_role

    def bet(self, forecast, odds):
        print(forecast, odds)
        betting_inputs = [f*o for f, o in zip(forecast, odds)]
        print(betting_inputs)

        def decide_betting(i):
            return 0.01 * self.bank_role if i > 1.0 else 0.0

        bets = np.array([decide_betting(i) for i in betting_inputs])
        return bets
