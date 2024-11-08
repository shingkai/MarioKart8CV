from abc import ABC, abstractmethod
from contextlib import contextmanager
import logging
import sqlite3

from mk8cv.data.state import PlayerState, RaceDataRow

logging.getLogger().setLevel(logging.DEBUG)


class Database(ABC):
    def __init__(self) -> None:
        pass

    @abstractmethod
    def write_event(self,
                race_id: int,
                timestamp: int,
                player_id: int, 
                lap: int,
                position: int,
                coins: int,
                item_1: str,
                item_2: str):
        pass

    @abstractmethod
    def get_previous_events(self,
                           race_id: int,
                           player_id: int,
                           num_rows: int = 1) -> list[PlayerState]:
        pass

class SqliteDB:
    def __init__(self, db_file: str = 'mk8cv.db', race_data_table: str = 'race_data') -> None:
        self.db_file = db_file
        self.race_data_table = race_data_table

    @contextmanager
    def get_connections(self):
        conn = sqlite3.connect(self.db_file)
        try:
            yield conn
        finally:
            conn.close()

    def write_event(self,
                    race_id: int,
                    timestamp: int,
                    player_id: int, 
                    lap: int,
                    position: int,
                    coins: int,
                    item_1: str,
                    item_2: str):
        with self.get_connections() as conn:
            cursor = conn.cursor()

            row = {
                'race_id': race_id,
                'timestamp': timestamp,
                'player_id': player_id,
                'lap': lap,
                'position': position,
                'coins' : coins,
                'item_1': item_1,
                'item_2': item_2
            }

            logging.debug(f"Inserting row {row}")

            cursor.execute(
                f'''
                INSERT INTO {self.race_data_table}
                (race_id, timestamp, player_id, lap, position, coins, item_1, item_2)
                VALUES (:race_id, :timestamp, :player_id, :lap, :position, :coins, :item_1, :item_2);
                ''', row)
            conn.commit()


    def get_previous_events(self,
                        race_id: int,
                        player_id: int,
                        num_rows: int = 1):
        with self.get_connections() as conn:
            cursor = conn.cursor()

            logging.debug(f"getting previous events for race_id: {race_id}, player_id: {player_id}")

            cursor.execute(
                f'''
                SELECT *
                FROM {self.race_data_table}
                WHERE race_id = ? AND player_id = ?
                ORDER BY timestamp DESC
                LIMIT ?;
                ''', (race_id, player_id, num_rows))
            result = cursor.fetchall()

            player_states = []
            for row in result:
                player_state = RaceDataRow(row).to_player_state()
                logging.debug(player_state)
                player_states.append(player_state)

            return player_states
