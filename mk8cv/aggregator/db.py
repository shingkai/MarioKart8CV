from abc import ABC, abstractmethod
from contextlib import contextmanager
import logging
import sqlite3

from mk8cv.data.state import PlayerState, Item

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

class SqliteDB(Database):
    def __init__(self, db_file: str = 'mk8cv.db', schema_file: str = r'./mk8cv-db/schema.sql',
                 race_data_table: str = 'race_data') -> None:
        super().__init__()
        self.db_file = db_file
        self.race_data_table = race_data_table
        self.create_tables(schema_file)

    def create_tables(self, schema_file: str):
        logging.info(f"Creating tables from schema file {schema_file}")
        with self.get_connections() as conn:
            cursor = conn.cursor()

            with open(schema_file, 'r') as f:
                cursor.executescript(f.read())
            conn.commit()
        logging.info("Tables created")

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
                INSERT OR REPLACE INTO {self.race_data_table}
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



class RaceDataRow:
    def __init__(self, row: tuple):
        self.race_id = row[0]
        self.timestamp = row[1]
        self.player_id = row[2]
        self.lap = row[3]
        self.position = row[4]
        self.coins = row[5]
        self.item_1 = row[6]
        self.item_2 = row[7]

    def to_player_state(self):
        return PlayerState(
            position=self.position,
            item1=Item[self.item_1],
            item2=Item[self.item_2],
            coins=self.coins,
            lap_num=self.lap) # TODO: decide if race-laps should be populated or left default

