import argparse
import json
import logging
from typing import Any

import redis

from mk8cv.aggregator.anomaly_correction import AnomalyCorrector, SlidingWindowAnomalyCorrector
from mk8cv.data.state import PlayerState, Item
from db import Database, SqliteDB

logging.getLogger().setLevel(logging.DEBUG)


class EventAggregater:
    def __init__(self, host: str, port: int, channel: str) -> None:
        self.host = host
        self.port = port
        self.redis_client = redis.Redis(host=host, port=port, db=0)
        self.channel = channel
        self.database: Database = SqliteDB()
        self.anomalyCorrector: AnomalyCorrector = SlidingWindowAnomalyCorrector(self.database, window_size=5);


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
            player_data = event[key]
            player_id = device_id * 2 + i

            player_state = PlayerState( player_data['position'],
                                        Item[player_data['item1']],
                                        Item[player_data['item2']],
                                        player_data['coins'],
                                        player_data['lap'])
            
            corrected_state = self.anomalyCorrector.correct_anomalies(frame_number, player_id, player_state)

            if (corrected_state):
                self.database.write_event(race_id,
                                        frame_number,
                                        player_id,
                                        corrected_state.lap,
                                        corrected_state.position,
                                        corrected_state.coins,
                                        corrected_state.item1.name,
                                        corrected_state.item2.name)



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
