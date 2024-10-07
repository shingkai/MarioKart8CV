import json
import random
from collections import Counter
from enum import Enum

import redis


class Player(str, Enum):
    P1 = 'p1'
    P2 = 'p2'


class Stat(str, Enum):
    POSITION = 'position'
    LAP = 'lap'
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


class PlayerState:
    def __init__(self, position: int, item1: Item, item2: Item, coins: int = 0, lap: int = 1):
        self.lap = lap
        self.position = position
        self.item1 = item1
        self.item2 = item2
        self.coins = coins

    def to_dict(self) -> dict[str, any]:
        return {
            Stat.COINS: self.coins,
            Stat.LAP: self.lap,
            Stat.POSITION: self.position,
            Stat.ITEM1: self.item1,
            Stat.ITEM2: self.item2,
        }
    
    @classmethod
    def from_dict(self, data: dict[Stat, any]):
        return PlayerState(
            data[Stat.POSITION],
            data[Stat.ITEM1],
            data[Stat.ITEM2],
            data[Stat.COINS],
            data[Stat.LAP])


class StateMessage:
    def __init__(self, device_id: int, frame_number: int, race_id: int, player1_state: dict[str, any],
                 player2_state: dict[str, any]):
        self.race_id = race_id
        self.device_id = device_id
        self.frame_number = frame_number
        self.player1_state = player1_state
        self.player2_state = player2_state

    def to_json(self) -> str:
        return json.dumps({
            "race_id": self.race_id,
            "device_id": self.device_id,
            "frame_number": self.frame_number,
            Player.P1: self.player1_state,
            Player.P2: self.player2_state
        })

    @staticmethod
    def generate_random_state():
        return {
            Stat.POSITION: random.randint(1, 12),
            Stat.ITEM1: random.choice(list(Item)),
            Stat.ITEM2: random.choice(list(Item)),
            Stat.COINS: random.randint(0, 10),
            Stat.LAP: random.randint(1, 3)
        }


# Option 1: Redis Pub/Sub
def publish_to_redis(redis_client: redis.Redis, channel: str, message: StateMessage):
    redis_client.publish(channel, message.to_json())
