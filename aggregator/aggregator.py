import argparse
import json
import redis
from typing import Dict, Any


class StateAggregator:
    def __init__(self, event_source: str, host: str = 'localhost', port: int = 6379):
        self.event_source = event_source
        self.host = host
        self.port = port
        self.redis_client = redis.Redis(host=self.host, port=self.port, db=0)
        self.player_stats: Dict[str, Dict[str, Any]] = {}  # Player ID -> Stats

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
            player_state = state_data[f'player{player_num}_state']
            player_id = f"{device_id}_{player_num}"

            if player_id not in self.player_stats:
                self.player_stats[player_id] = {
                    'total_frames': 0,
                    'positions': [],
                    'items': {},
                }

            stats = self.player_stats[player_id]
            stats['total_frames'] += 1
            stats['positions'].append(player_state['position'])
            item = player_state['item']
            stats['items'][item] = stats['items'].get(item, 0) + 1

        self._print_current_stats(frame_number)

    def _print_current_stats(self, frame_number: int):
        print(f"\nCurrent Stats (Frame {frame_number}):")
        for player_id, stats in self.player_stats.items():
            print(f"Player {player_id}:")
            print(f"  Total Frames: {stats['total_frames']}")
            print(f"  Average Position: {sum(stats['positions']) / len(stats['positions']):.2f}")
            print(f"  Item Distribution: {stats['items']}")
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
