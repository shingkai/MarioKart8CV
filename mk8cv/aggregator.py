import argparse
import json
import redis
from typing import Dict, Any
from collections import Counter

from state import Item


class PlayerPositions:
    def __init__(self):
        self.distribution = Counter()
        self.frames: list[(int, int)] = [(-1, -1)] # number of frames, position


class PlayerItems:
    def __init__(self):
        self.first_slot_distribution = Counter()
        self.second_slot_distribution = Counter()
        self.frames: list[(int, Item, Item)] = [(-1, Item.NONE, Item.NONE)] # number of frames, item1, item2


class PlayerCoins:
    def __init__(self):
        self.distribution = Counter()
        self.frames: list[tuple[int, int]] = [(-1, -1)] # number of frames, coins


class PlayerStats:
    def __init__(self, _id: str):
        self.id = _id
        self.total_frames = 0
        self.positions = PlayerPositions()
        self.items = PlayerItems()
        self.coins = PlayerCoins()


    def get_frames_in_position(self, position: int) -> int:
        pass

    def get_frames_with_items(self, item1: Item, item2: Item) -> int:
        pass

    def get_frames_with_coins(self, coins: int) -> int:
        pass

class StateAggregator:
    def __init__(self, event_source: str, host: str = 'localhost', port: int = 6379):
        self.event_source = event_source
        self.host = host
        self.port = port
        self.redis_client = redis.Redis(host=self.host, port=self.port, db=0)
        self.player_stats: Dict[str, PlayerStats] = {}  # Player ID -> Stats

    def start(self):
        if self.event_source == 'redis':
            self._listen_redis()
        else:
            raise ValueError(f"Unsupported event source: {self.event_source}")

    def _listen_redis(self):
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe('mario_kart_states')
        print(f"Listening for events on Redis channel 'mario_kart_states'...")

        for message in pubsub.listen():
            if message['type'] == 'message':
                self._process_message(json.loads(message['data']))

    def _process_message(self, state_data: Dict[str, Any]):
        device_id = state_data['device_id']
        frame_number = state_data['frame_number']

        for player_num in [1, 2]:
            player_state = state_data[f'player{player_num}']
            player_id = f"{device_id}_{player_num}"

            if player_id not in self.player_stats:
                self.player_stats[player_id] = PlayerStats(player_id)

            stats: PlayerStats = self.player_stats[player_id]

            # handle race position
            if 'position' in player_state:
                if stats.positions.frames[-1][1] != player_state['position']:
                    stats.positions.frames.append((1, player_state['position']))
                else:
                    stats.positions.frames[-1][0] += 1
                stats.positions.distribution[player_state['position']] += 1
            else:
                # if we didn't receive position, we'll just assume it didn't change
                stats.positions.distribution[stats.positions.frames[-1][1]] += 1
                stats.positions.frames[-1][0] += 1

            # handle coins
            if 'coins' in player_state:
                stats.coins.distribution[player_state['coins']] += 1
                if stats.coins.frames[-1][1] != player_state['coins']:
                    stats.coins.frames[-1] = (stats.coins.frames[-1][0] + 1, stats.coins.frames[-1][1]))
                else:
                    stats.coins.frames[-1][0] += 1
                stats.coins.distribution[player_state['coins']] += 1
            else:
                # if we didn't receive coins, we'll just assume they didn't change
                stats.coins.distribution[stats.coins.frames[-1][1]] += 1
                stats.coins.frames[-1][0] += 1

            # handle items
            if 'items' in player_state:
                items = player_state['items']
                stats.items.first_slot_distribution[items[0]] += 1
                stats.items.second_slot_distribution[items[1]] += 1
                if stats.items.frames[-1][1] != items[0] or stats.items.frames[-1][2] != items[1]:
                    stats.items.frames.append((1, items[0], items[1]))
                else:
                    stats.items.frames[-1][0] += 1
            else:
                # if we didn't receive items, we'll just assume they didn't change
                stats.items.first_slot_distribution[stats.items.frames[-1][1]] += 1
                stats.items.second_slot_distribution[stats.items.frames[-1][2]] += 1
                stats.items.frames[-1][0] += 1

            stats.total_frames += 1

        self._print_current_stats(frame_number)

    def _print_current_stats(self, frame_number: int):
        print(f"\nCurrent Stats (Frame {frame_number}):")
        for player_id, stats in self.player_stats.items():
            print(f"Player {player_id}:")
            print(f"  Total Frames: {stats.total_frames}")
            if len(stats.positions.distribution) > 0:
                print(f"  Average Position: {sum(stats.positions.distribution) / len(stats.positions.distribution):.2f}")
            print(f"  Position Distribution: {stats.positions.distribution}")
            if len(stats.coins.distribution) > 0:
                print(f"  Average Coins: {sum(stats.coins.distribution) / len(stats.coins.distribution):.2f}")
            print(f"  First-Slot Item Distribution: {stats.items.first_slot_distribution}")
            print(f"  Second-Slot Item Distribution: {stats.items.second_slot_distribution}")
        print("\n" + "=" * 40 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Mario Kart 8 State Aggregator")
    parser.add_argument('--event-source', type=str, default='redis', choices=['redis'],
                        help='Event source to listen to (currently only redis is supported)')
    parser.add_argument('--host', type=str, default='localhost',
                        help='Host for the event source')
    parser.add_argument('--port', type=int, default=6379,
                        help='Port for the event source')

    args = parser.parse_args()

    aggregator = StateAggregator(args.event_source, args.host, args.port)

    try:
        aggregator.start()
    except KeyboardInterrupt:
        print("Aggregator stopped.")


if __name__ == "__main__":
    main()
