from abc import ABC


class Evaluator(ABC):

    def __init__(self, **kwargs):
        self.outcomes = kwargs.get("outcomes")



