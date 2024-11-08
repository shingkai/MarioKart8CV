import json
import random
from enum import Enum


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

    @staticmethod
    def get(name: str, default=None):
        try:
            return Item[name.upper().replace(' ', '_')]
        except KeyError:
            return default

    def __str__(self):
        return self.name.lower().replace('_', ' ')

    def __repr__(self):
        return self.__str__()

class StateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Item):
            return str(obj.name)
        elif isinstance(obj, PlayerState):
            return {
                'lap': obj.lap,
                'race_laps': obj.race_laps,
                'position': obj.position,
                'item1': obj.item1.name,
                'item2': obj.item2.name,
                'coins': obj.coins
            }
        elif isinstance(obj, StateMessage):
            return {
                'race_id': obj.race_id,
                'device_id': obj.device_id,
                'frame_number': obj.frame_number,
                'player1_state': obj.player1_state,
                'player2_state': obj.player2_state
            }
        else:
            return super().default(obj)


class StateDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        super().__init__(object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):
        # Decode PlayerState
        if 'lap' in obj and 'race_laps' in obj and 'position' in obj:
            return PlayerState(
                lap=obj['lap'],
                race_laps=obj['race_laps'],
                position=obj['position'],
                item1=Item[obj['item1']],  # assuming Item is an Enum
                item2=Item[obj['item2']],
                coins=obj['coins']
            )

        # Decode StateMessage
        if 'race_id' in obj and 'device_id' in obj and 'frame_number' in obj:
            return StateMessage(
                race_id=obj['race_id'],
                device_id=obj['device_id'],
                frame_number=obj['frame_number'],
                player1_state=obj['player1_state'],
                player2_state=obj['player2_state']
            )

        return obj


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
            Stat.ITEM1: self.item1.name,
            Stat.ITEM2: self.item2.name,
            Stat.COINS: self.coins,
            Stat.RACE_LAPS: self.race_laps
        }, cls=StateEncoder)


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
            "race_id": self.race_id,
            "device_id": self.device_id,
            "frame_number": self.frame_number,
            Player.P1: self.player1_state if self.player1_state else {},
            Player.P2: self.player2_state if self.player2_state else {}
        }, cls=StateEncoder)


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

