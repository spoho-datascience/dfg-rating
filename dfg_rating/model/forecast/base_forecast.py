from abc import ABC, abstractmethod
from typing import List


class BaseForecast(ABC):

    """Abstract class defining the interface of Forecast object.

    Attributes:
        type: Text descriptor of the forecast type.
        outcomes: List of outcomes.
    """

    def __init__(self, type: str, outcomes: List[str], probs: List[float]):
        self.type = type
        self.outcomes = outcomes
        self.probs = probs