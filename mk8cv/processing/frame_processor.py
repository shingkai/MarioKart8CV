import json
import logging
import os

import cv2
from multiprocessing import Event, Queue
from queue import Empty
import time

from mk8cv.models.position_classifier import PositionClassifier
from mk8cv.models.item_classifier import ItemClassifier
from mk8cv.sinks.sink import SinkType
from mk8cv.data.state import Player, StateMessage, publish_to_redis, Stat, PlayerState, Item

from mk8cv.processing.ocr import extract_coins, extract_laps
from mk8cv.processing.aois import CROP_COORDS

import redis

from mk8cv.utils.visualization import add_text, visualize


def generateCrops(device_id: int, frame_count: int, frame: cv2.typing.MatLike, training_save_dir: str) -> None:
    # formatted as "crop_nome" : (x1, x2, y1, y2)
    height, width, channels = frame.shape

    for player, stat in CROP_COORDS.items():
        for name, coords in stat.items():
            crop = frame[round(height * coords[2]) : round(height * coords[3]), round(width * coords[0]) : round(width * coords[1])]
            out_path = os.path.join(training_save_dir, name, str(player))
            os.makedirs(out_path, exist_ok=True)
            cv2.imwrite(os.path.join(out_path, f'{frame_count:06}.png'), crop)

    # out_path = os.path.join(training_save_dir, "frames", str(device_id))
    # os.makedirs(out_path, exist_ok=True)
    # cv2.imwrite(os.path.join(out_path, f'{frame_count:06}.png'), frame)


def process_frames(
        process_queue: Queue, stop_event: Event, display: bool,
        training_save_dir: str,
        sink_type: SinkType = SinkType.REDIS,
        extract: list[Stat] = None
) -> None:
    logging.getLogger().setLevel(logging.INFO)
    logging.info("Starting frame processor...")
    if extract is None:
        extract = [stat for stat in Stat]
    match sink_type:
        case SinkType.REDIS:
            sink = redis.Redis()
        case _:
            sink = None
    logging.getLogger().setLevel(logging.INFO)
    start_time = time.time()
    frames_processed = 0
    if Stat.ITEM1 in extract or Stat.ITEM2 in extract:
        # TODO: read the model type from config or args
        from mk8cv.models.item_classifier import MobileNetV3ItemClassifier
        item_model: ItemClassifier = MobileNetV3ItemClassifier()
        item_model.load()

    if Stat.POSITION in extract:
        # from mk8cv.models.position_classifier import MobileNetV3PositionClassifier
        # position_model: PositionClassifier = MobileNetV3PositionClassifier()
        # from mk8cv.models.position_classifier import TemplatePositionClassifier
        # position_model: PositionClassifier = TemplatePositionClassifier()
        from mk8cv.models.position_classifier import CannyMaskPositionClassifier
        position_model: PositionClassifier = CannyMaskPositionClassifier()
        position_model.load()

    with open('item_annotations.json', 'w') as f:
        logging.info('Starting frame processing loop...')
        while not stop_event.is_set():
            try:
                device_id, frame_count, frame = process_queue.get(timeout=1)

                race_id = 0  # This will need to be extracted from our CV thingy

                if frame_count % 6000 == 0:
                    race_id += 1

                if extract is None or not extract:
                    player1_state = PlayerState.generate_random_state()
                    player2_state = PlayerState.generate_random_state()
                else:
                    player1_state = PlayerState(-1, Item.NONE, Item.NONE, -1, -1, -1)
                    player2_state = PlayerState(-1, Item.NONE, Item.NONE, -1, -1, -1)

                if Stat.COINS in extract:
                    player1_state.coins = extract_coins(frame, Player.P1)
                    player2_state.coins = extract_coins(frame, Player.P2)

                if Stat.LAP_NUM or Stat.RACE_LAPS in extract:
                    player1_state.lap, player1_state.race_laps = extract_laps(frame, Player.P1)
                    player2_state.lap, player2_state.race_laps = extract_laps(frame, Player.P2)

                if Stat.ITEM1 in extract or Stat.ITEM2 in extract:
                    player1_state.item1, player1_state.item2 = item_model.extract_player_items(frame, Player.P1)
                    player2_state.item1, player2_state.item2 = item_model.extract_player_items(frame, Player.P2)

                if Stat.POSITION in extract:
                    player1_state.position = position_model.extract_player_position(frame, Player.P1)
                    player2_state.position = position_model.extract_player_position(frame, Player.P2)

                state_message = StateMessage(device_id, frame_count, race_id, player1_state, player2_state)

                f.write(json.dumps(state_message, default=str))

                # Choose one of the following based on your chosen method:
                match sink_type:
                    case SinkType.REDIS:
                        publish_to_redis(sink, "mario_kart_states", state_message)
                    case _:
                        logging.debug("state_message: %s", json.dumps(state_message, default=str))

                frames_processed += 1
                elapsed_time = time.time() - start_time
                if elapsed_time >= 1.0:
                    fps = frames_processed / elapsed_time
                    logging.info(f"Processing FPS: {fps:.2f}")
                    frames_processed = 0
                    start_time = time.time()

                logging.debug(f"Processed and published frame {frame_count} from device {device_id}")
                if training_save_dir:
                    generateCrops(device_id=device_id, frame_count=frame_count, frame=frame,
                                  training_save_dir=training_save_dir)

                states = {
                    Player.P1: player1_state,
                    Player.P2: player2_state
                }

                if display:
                    visualize(frame, states, device_id, stop_event)

            except Empty:
                print('empty')
                logging.info("Queue is empty. Waiting for frames...")
                stop_event.set()
                continue
