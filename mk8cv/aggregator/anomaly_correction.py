from abc import ABC, abstractmethod

from mk8cv.data.state import PlayerState, Item
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
        self.history: dict[int, dict[int, PlayerState]] = {} # playerId -> ( timestamp -> PlayerState )

    def correct_anomalies(self, timestamp: int, player_id: int, state: PlayerState) -> PlayerState:
        # correct anomalies in PlayerState
        corrected_position = self.correctPosition(state.position, timestamp, player_id)
        corrected_item1 = state.item1
        corrected_item2 = state.item2
        corrected_coins = state.coins
        corrected_lap = state.lap
        corrected_race_laps = state.race_laps

        corrected_state = PlayerState(corrected_position, corrected_item1, corrected_item2, corrected_coins, corrected_lap, corrected_race_laps)

        # add the new record to the history
        if player_id not in self.history:
            self.history[player_id] = {}
        if timestamp not in self.history[player_id]:
            self.history[player_id][timestamp] = state

        # check if the self.history has more than self.window_size entries. If it does, remove the oldest entries until it is the same size
        while len(self.history) > self.window_size:
            oldest_timestamp = min(self.history.keys())
            del self.history[oldest_timestamp]

        print(f'{len(self.history)} : {timestamp}')

        return corrected_state
    

    def correctPosition(self, position: int, timestamp: int, player_id: int) -> int:
        if position != 0:
            return position
        else:
            previous_state = self.history[player_id][list(self.history.keys())[len(self.history) - 1]]
            corrected_position = previous_state.position
            print(f"correcting position from 0 to {corrected_position}")
            return corrected_position
