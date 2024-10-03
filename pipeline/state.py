import json
import random
from collections import Counter
from enum import Enum

import redis
import pika


class Item(Enum):
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
    def __init__(self, position: int, items: tuple[Item, Item], coins: int = 0, lap: int = 1):
        self.lap = lap
        self.position = position
        self.items = items
        self.item_distribution = Counter()
        self.coins = coins

    def to_dict(self) -> dict[str, any]:
        return {
            "coins": self.coins,
            "lap": self.lap,
            "position": self.position,
            "items": self.items,
            "item_distribution": self.item_distribution
        }


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
            "player1_state": self.player1_state,
            "player2_state": self.player2_state
        })

    @staticmethod
    def generate_random_state():
        return {
            "position": random.randint(1, 12),
            "items": (random.choice(list(Item)), random.choice(list(Item))),
            "coins": random.randint(0, 10),
            "lap": random.randint(1, 3)
        }


# Option 1: Redis Pub/Sub
def publish_to_redis(redis_client: redis.Redis, channel: str, message: StateMessage):
    redis_client.publish(channel, message.to_json())


# Option 2: RabbitMQ
def publish_to_rabbitmq(channel: pika.channel.Channel, routing_key: str, message: StateMessage):
    channel.basic_publish(exchange='', routing_key=routing_key, body=message.to_json())
