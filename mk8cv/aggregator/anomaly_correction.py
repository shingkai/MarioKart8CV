from abc import ABC, abstractmethod

from mk8cv.data.state import PlayerState
from db import Database

class AnomalyCorrector(ABC):
    def __init__(self) -> None:
        pass

    @abstractmethod
    def correct_anomalies(self, player_id: int, state: PlayerState) -> PlayerState:
        pass


class SlidingWindowAnomalyCorrector(AnomalyCorrector):
    """
    A sliding-window based approach to anomaly correction. For a given player, a sliding
    window is maintained and used to detect anomolous values, using the following rules:
    - if a non-item value is None, use the previous value
    - if lap

    """

    def __init__(self, database: Database, window_size: int = 5) -> None:
        self.database = database
        self.window_size = window_size
        self.history: dict[int, list[PlayerState]] = {}

    def correct_anomalies(self, player_id: int, state: PlayerState) -> PlayerState:
