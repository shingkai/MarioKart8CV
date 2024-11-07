from contextlib import contextmanager
import logging
import sqlite3

from mk8cv.data.state import PlayerState

logging.getLogger().setLevel(logging.DEBUG)


class SqliteDB:
    def __init__(self, db_file: str = 'mk8cv.db'):
        self.db_file = db_file

    @contextmanager
    def get_connections(self):
        conn = sqlite3.connect(self.db_file)
        try:
            yield conn
        finally:
            conn.close()

    def write_event(self,
                    race_id: str,
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
                '''
                INSERT INTO race_data (race_id, timestamp, player_id, lap, position, coins, item_1, item_2)
                VALUES (:race_id, :timestamp, :player_id, :lap, :position, :coins, :item_1, :item_2);
                ''', row)
            conn.commit()
