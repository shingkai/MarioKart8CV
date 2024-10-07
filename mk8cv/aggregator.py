import argparse
import json
import redis
from typing import Dict, Any, Optional, TypeVar, Generic
from collections import Counter

from state import Item, Stat, Player

T = TypeVar('T')

class RunLengthEncodedStat(Generic[T]):
    def __init__(self, initial_value: T):
        self.distribution: Counter[T] = Counter()
        self.frames: list[tuple[int, T]] = [(-1, initial_value)]  # number of frames, stat
        self.total_frames: int = 0

    def update(self, stat: Optional[T] = None):
        self.total_frames += 1
        if stat is not None:
            if self.frames[-1][1] != stat:
                self.frames.append((self.total_frames, stat))
            self.distribution[stat] += 1
        else:
            # if we didn't receive update, we'll just assume it didn't change
            self.distribution[self.frames[-1][1]] += 1

    def get_stat_at_frame(self, frame: int) -> T:
        for i, (start_frame, stat) in enumerate(self.frames):
            if i == len(self.frames) - 1 or self.frames[i+1][0] > frame:
                return stat
        raise ValueError(f"No stat data for frame {frame}")

    def get_frames_with_stat(self, stat: T) -> int:
        return self.distribution[stat]

    def __str__(self):
        return "\n".join([f"frames {start}-{self.frames[i+1][0] if i+1 < len(self.frames) else self.total_frames}: {stat}"
                          for i, (start, stat) in enumerate(self.frames)])


class PlayerItems(RunLengthEncodedStat[tuple[Item, Item]]):
    def __init__(self):
        super().__init__((Item.NONE, Item.NONE))
        self.first_slot_distribution: Counter[Item] = Counter()
        self.second_slot_distribution: Counter[Item] = Counter()

    def update(self, stat: Optional[tuple[Item, Item]] = None):
        super().update(stat)
        if stat is not None:
            self.first_slot_distribution[stat[0]] += 1
            self.second_slot_distribution[stat[1]] += 1

class PlayerCoins(RunLengthEncodedStat[int]):
    def __init__(self):
        super().__init__(-1)

class PlayerPositions(RunLengthEncodedStat[int]):
    def __init__(self):
        super().__init__(-1)


class PlayerStats:
    def __init__(self, _id: str):
        self.id: str = _id
        self.total_frames: int = 0
        self.positions = PlayerPositions()
        self.items: PlayerItems = PlayerItems()
        self.coins: PlayerCoins = PlayerCoins()


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

    def _process_message(self, state_data: dict[str, Any]):
        device_id = state_data['device_id']
        frame_number = state_data['frame_number']

        for key in Player:
            player_state = state_data[key]
            player_id = f"{device_id}_{key}"

            if player_id not in self.player_stats:
                self.player_stats[player_id] = PlayerStats(player_id)

            stats: PlayerStats = self.player_stats[player_id]

            stats.positions.update(player_state[Stat.POSITION])
            stats.items.update((Item(player_state[Stat.ITEM1]), Item(player_state[Stat.ITEM2])))
            stats.coins.update(player_state[Stat.COINS])

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
