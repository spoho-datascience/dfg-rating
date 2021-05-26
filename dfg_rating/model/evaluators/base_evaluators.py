from abc import ABC, abstractmethod


class Evaluator(ABC):

    def __init__(self, **kwargs):
        self.outcomes = kwargs.get("outcomes")

    @abstractmethod
    def eval(self, match_attributes):
        pass



