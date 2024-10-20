import json
import random
from enum import Enum

import redis


class Player(str, Enum):
    P1 = 'p1'
    P2 = 'p2'


class Stat(str, Enum):
    POSITION = 'position'
    LAP_NUM = 'lap_num'
    RACE_LAPS = 'race_laps'
    COINS = 'coins'
    ITEM1 = 'item1'
    ITEM2 = 'item2'


class Item(int, Enum):
    BANANA = 1
    TRIPLE_BANANA = 2
    GREEN_SHELL = 3
    TRIPLE_GREEN_SHELL = 4
    RED_SHELL = 5
    TRIPLE_RED_SHELL = 6
    BLUE_SHELL = 7
    BOB_OMB = 8
    MUSHROOM = 9
    TRIPLE_MUSHROOM = 10
    GOLDEN_MUSHROOM = 11
    BULLET_BILL = 12
    BLOOPER = 13
    LIGHTNING = 14
    STAR = 15
    FIRE_FLOWER = 16
    BOOMERANG = 17
    PIRANHA_PLANT = 18
    SUPER_HORN = 19
    CRAZY_EIGHT = 20
    COIN = 21
    FEATHER = 22
    BOO = 23
    NONE = 24

    def __str__(self):
        return self.name.lower().replace('_', ' ')

    def __repr__(self):
        return self.__str__()


class PlayerState:
    def __init__(self, position: int, item1: Item, item2: Item, coins: int = 0, lap_num: int = 1, race_laps: int = 3):
        self.lap = lap_num
        self.race_laps = race_laps
        self.position = position
        self.item1 = item1
        self.item2 = item2
        self.coins = coins

    @staticmethod
    def generate_random_state():
        return PlayerState(
            position=random.randint(1, 12),
            item1=random.choice(list(Item)),
            item2=random.choice(list(Item)),
            coins=random.randint(0, 10),
            lap_num=random.randint(1, 3),
            race_laps=3
        )

    def __repr__(self):
        return json.dumps({
            Stat.POSITION: self.position,
            Stat.LAP_NUM: self.lap,
            Stat.ITEM1: self.item1,
            Stat.ITEM2: self.item2,
            Stat.COINS: self.coins,
            Stat.RACE_LAPS: self.race_laps
        }, default=str)


class StateMessage:
    def __init__(self, device_id: int, frame_number: int, race_id: int, player1_state: PlayerState,
                 player2_state: PlayerState):
        self.race_id = race_id
        self.device_id = device_id
        self.frame_number = frame_number
        self.player1_state = player1_state
        self.player2_state = player2_state

    def __repr__(self):
        return json.dumps({
            # "race_id": self.race_id,
            # "device_id": self.device_id,
            "frame_number": self.frame_number,
            Player.P1: self.player1_state if self.player1_state else {},
            Player.P2: self.player2_state if self.player2_state else {}
        }, default=str)

# Option 1: Redis Pub/Sub
def publish_to_redis(redis_client: redis.Redis, channel: str, message: StateMessage):
    redis_client.publish(channel, json.dumps(message, default=str))
