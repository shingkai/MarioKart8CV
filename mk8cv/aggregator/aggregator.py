import argparse
import json
import logging
from typing import Any

import redis

from mk8cv.data.state import PlayerState
from db import SqliteDB

logging.getLogger().setLevel(logging.DEBUG)


class EventAggregater:
    def __init__(self, host: str, port: int, channel: str) -> None:
        self.host = host
        self.port = port
        self.redis_client = redis.Redis(host=host, port=port, db=0)
        self.channel = channel
        self.database = SqliteDB()


    def listen(self) -> None:
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe(self.channel)

        for message in pubsub.listen():
            if message['type'] == 'message':
                logging.debug(f"Message received {message}")
                self._process_event(json.loads(message['data']))


    def _process_event(self, event: dict[str, Any]) -> None:
        race_id = event['race_id']
        device_id = event['device_id']
        frame_number = event['frame_number']

        for i, key in [(1, "player1_state"), (2, "player2_state")]:
            player_state = event[key]
            player_id = device_id * 2 + i

            self.database.write_event(race_id,
                                      frame_number,
                                      player_id,
                                      player_state['lap'],
                                      player_state['position'],
                                      player_state['coins'],
                                      player_state['item1'],
                                      player_state['item2'])



def main():
    parser = argparse.ArgumentParser(description="Mario Kart 8 State Aggregator")
    parser.add_argument('--host', type=str, default='localhost',
                        help='Host for the event source')
    parser.add_argument('--port', type=int, default=6379,
                        help='Port for the event source')
    parser.add_argument('--channel', type=str, default='mario_kart_states',
                        help='Redis channel to listen on')

    args = parser.parse_args()

    aggregator = EventAggregater(args.host, args.port, args.channel)

    try:
        aggregator.listen()
    except KeyboardInterrupt:
        logging.info("Aggregator stopped.")


if __name__ == "__main__":
    main()
