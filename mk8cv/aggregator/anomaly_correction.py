from abc import ABC, abstractmethod
import logging
from collections import Counter

from mk8cv.data.state import PlayerState, Item
from db import Database

logging.getLogger().setLevel(logging.DEBUG)

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


    """

    def __init__(self, database: Database, window_size: int = 5) -> None:
        self.database = database
        self.window_size = window_size
        self.history: dict[int, dict[int, PlayerState]] = {} # playerId -> ( timestamp -> PlayerState )

    def correct_anomalies(self, timestamp: int, player_id: int, state: PlayerState) -> PlayerState:

        corrected_position = self.correctPosition(state.position, timestamp, player_id)
        corrected_item1 : Item = state.item1
        corrected_item2 : Item = state.item2
        corrected_coins = state.coins
        corrected_lap = state.lap
        corrected_race_laps = state.race_laps

        corrected_state = PlayerState(corrected_position, corrected_item1, corrected_item2, corrected_coins, corrected_lap, corrected_race_laps)

        # add the new record to the history
        if player_id not in self.history:
            self.history[player_id] = {}
        if timestamp not in self.history[player_id]:
            self.history[player_id][timestamp] = corrected_state

        # check if the self.history[player_id] has more than self.window_size entries. If it does, remove the oldest entries until it is the same size
        while len(self.history[player_id]) > self.window_size:
            oldest_timestamp = min(self.history[player_id].keys())
            del self.history[player_id][oldest_timestamp]

        published_state = PlayerState(
            Counter(past_state.position for past_state in self.history[player_id].values()).most_common(1)[0][0],
            Counter(past_state.item1 for past_state in self.history[player_id].values()).most_common(1)[0][0],
            Counter(past_state.item2 for past_state in self.history[player_id].values()).most_common(1)[0][0],
            Counter(past_state.coins for past_state in self.history[player_id].values()).most_common(1)[0][0],
            Counter(past_state.lap for past_state in self.history[player_id].values()).most_common(1)[0][0],
            Counter(past_state.race_laps for past_state in self.history[player_id].values()).most_common(1)[0][0]
        )

        return published_state
    

    def correctPosition(self, position: int, timestamp: int, player_id: int) -> int:
        # if position is 0 then us the previous position
        if position != 0:
            return position
        else:
            previous_state = self.history[player_id][list(self.history[player_id].keys())[len(self.history[player_id]) - 1]]
            corrected_position = previous_state.position
            logging.debug(f"correcting position from 0 to {corrected_position}")
            return corrected_position
