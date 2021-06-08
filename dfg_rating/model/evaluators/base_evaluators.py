from abc import ABC, abstractmethod
from typing import List


class Evaluator(ABC):

    def __init__(self, **kwargs):
        self.outcomes = kwargs.get("outcomes")

    @abstractmethod
    def eval(self, match_attributes):
        pass


class BettingActivity(Evaluator):

    def __init(self, **kwargs):
        super().__init__(**kwargs)
        self.player_name = kwargs.get("player_name")

    def eval(self, match_attributes):
        bets: List[float] = match_attributes['bets'][self.player_name]
        betting_activity = {
            "qty": len(bets)
        }
        return 1, betting_activity
