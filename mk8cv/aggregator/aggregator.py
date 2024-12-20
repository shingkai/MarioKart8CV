import argparse
import json
import logging
from typing import Any

import redis

from mk8cv.aggregator.anomaly_correction import AnomalyCorrector, SlidingWindowAnomalyCorrector
from mk8cv.data.state import PlayerState, Item
from db import Database, SqliteDB

import signal

logging.getLogger().setLevel(logging.DEBUG)


class EventAggregator:
    def __init__(self, host: str, port: int, channel: str) -> None:
        self.host = host
        self.port = port
        self.redis_client = redis.Redis(host=host, port=port, db=0)
        self.channel = channel
        self.database: Database = SqliteDB()
        self.anomaly_corrector: AnomalyCorrector = SlidingWindowAnomalyCorrector(self.database, window_size=9);
        self.previous_state: dict[int, PlayerState] = {} # playerId -> PlayerState
        self.running = True

        # Set up signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, _):
        """Handle shutdown signals"""
        logging.info(f"Received signal {signum}. Shutting down...")
        self.running = False

    def listen(self) -> None:
        logging.info(f"Listening on {self.host}:{self.port} on channel {self.channel}")
        logging.info(f"redis_client.ping(): {self.redis_client.ping()}")
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe(self.channel)

        try:
            while self.running:
                message = pubsub.get_message(timeout=1.0)  # Use timeout to check running flag periodically
                if message and message['type'] == 'message':
                    logging.debug(f"Message received {message}")
                    self._process_event(json.loads(message['data']))
        finally:
            # Clean up
            pubsub.unsubscribe()
            pubsub.close()
            self.redis_client.close()
            logging.info("Cleaned up Redis connections")

    def _process_event(self, event: dict[str, Any]) -> None:
        race_id = event['race_id']
        device_id = event['device_id']
        frame_number = event['frame_number']

        for i, key in [(1, "player1_state"), (2, "player2_state")]:
            player_data = event[key]
            player_id = device_id * 2 + i

            if player_id not in self.previous_state:
                self.previous_state[player_id] = None

            player_state = PlayerState( player_data['position'],
                                        Item[player_data['item1']],
                                        Item[player_data['item2']],
                                        player_data['coins'],
                                        player_data['lap'])
            
            corrected_state = self.anomaly_corrector.correct_anomalies(frame_number, player_id, player_state)

            # if corrected_state is not None and differs from the previous_state, publish it and set it as the new previous_state
            if (corrected_state and self.previous_state[player_id] != corrected_state):
                logging.debug(f"Writing event for race {race_id}, frame {frame_number}, player {player_id}")
                self.database.write_event(race_id,
                                        frame_number,
                                        player_id,
                                        corrected_state.lap,
                                        corrected_state.position,
                                        corrected_state.coins,
                                        corrected_state.item1.name,
                                        corrected_state.item2.name)
                self.previous_state[player_id] = corrected_state


def main():
    parser = argparse.ArgumentParser(description="Mario Kart 8 State Aggregator")
    parser.add_argument('--host', type=str, default='localhost',
                        help='Host for the event source')
    parser.add_argument('--port', type=int, default=6379,
                        help='Port for the event source')
    parser.add_argument('--channel', type=str, default='mario_kart_states',
                        help='Redis channel to listen on')

    args = parser.parse_args()

    aggregator = EventAggregator(args.host, args.port, args.channel)

    try:
        aggregator.listen()
    except KeyboardInterrupt:
        logging.info("Aggregator stopped.")


if __name__ == "__main__":
    main()
