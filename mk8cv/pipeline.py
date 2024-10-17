import logging
from enum import Enum
import os
import cv2
import argparse
from multiprocessing import Process, Queue as ProcessQueue, Event
from queue import Full, Empty
import time
from typing import Optional, Tuple, Union


from state import Player, StateMessage, publish_to_redis, Stat
from ocr import extract_player_state, CROP_COORDS

import redis


def capture_and_process(
        source: Union[int, str],
        device_id: int,
        downscale_resolution: Tuple[int, int],
        frame_skip: int,
        process_queue: ProcessQueue,
        fps: Optional[float] = None
) -> None:
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"Error opening video source: {source}")
        return

    frame_time = None

    if isinstance(source, int):  # Real device
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    else:  # Video file
        frame_time = 1 / fps if fps else 0

    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            if isinstance(source, str):  # Video file
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Loop the video
                continue
            else:
                break

        frame_count += 1
        if frame_count % (frame_skip + 1) != 0:
            continue

        # Downscale to specified resolution
        downscaled = cv2.resize(frame, downscale_resolution)

        # Try to put the frame in the queue, if it's full, skip this frame
        try:
            process_queue.put((device_id, frame_count, downscaled), block=False)
        except Full:
            print(f"Queue is full. Skipping frame from device {device_id}")

        if isinstance(source, str) and frame_time:  # Video file
            time.sleep(frame_time)  # Simulate real-time capture


class SinkType(Enum):
    REDIS = 1

def add_text(frame: cv2.typing.MatLike, text: str, position: Tuple[int, int], color=(255, 0, 0), scale=2, thickness=5) -> None:
    cv2.putText(
        frame,
        text,
        position,
        cv2.FONT_HERSHEY_SIMPLEX,
        fontScale=scale,
        color=color,
        thickness=thickness
    )

# Modify the process_frames function to use one of these methods
def process_frames(
        process_queue: ProcessQueue, stop_event: Event, display: bool,
        training_save_dir: str,
        sink_type: SinkType = SinkType.REDIS,
        sink: Optional[redis.Redis] = None,
) -> None:
    while not stop_event.is_set():
        try:
            device_id, frame_count, frame = process_queue.get(timeout=1)

            race_id = 0  # This will need to be extracted from our CV thingy

            if frame_count % 6000 == 0:
                race_id += 1

            player1_state = extract_player_state(frame, Player.P1)
            player2_state = extract_player_state(frame, Player.P2)

            state_message = StateMessage(device_id, frame_count, race_id, player1_state, player2_state)

            # Choose one of the following based on your chosen method:
            match sink_type:
                case SinkType.REDIS:
                    publish_to_redis(sink, "mario_kart_states", state_message)
                case _:
                    logging.info("state_message: %s", state_message.to_json())
            print(f"Processed and published frame {frame_count} from device {device_id}")
            if training_save_dir:
                generateCrops(device_id=device_id, frame_count=frame_count, frame=frame,
                              training_save_dir=training_save_dir)

            print(f"Processed frame {frame_count} from device {device_id}")

            states = {
                Player.P1: player1_state,
                Player.P2: player2_state
            }

            if display:
                for player in [Player.P1, Player.P2]:
                    crop_coords = CROP_COORDS[player]
                    coins_text_position = (
                        round(frame.shape[1] * crop_coords[Stat.COINS][0]),
                        round(frame.shape[0] * (crop_coords[Stat.COINS][2] - 0.015))
                    )
                    add_text(frame, f'{states[player].coins}', coins_text_position)

                    lap_text_position = (
                        round(frame.shape[1] * crop_coords[Stat.LAP_NUM][0]),
                        round(frame.shape[0] * (crop_coords[Stat.LAP_NUM][2] - 0.015))
                    )
                    add_text(frame, f'{states[player].lap}/{states[player].race_laps}', lap_text_position, scale=1, thickness=3)

                    position_text_position = (
                        round(frame.shape[1] * crop_coords[Stat.POSITION][0]),
                        round(frame.shape[0] * (crop_coords[Stat.POSITION][2] - 0.015))
                    )
                    add_text(frame, f'{states[player].position}', position_text_position)

                    item1_text_position = (
                        round(frame.shape[1] * crop_coords[Stat.ITEM1][0]),
                        round(frame.shape[0] * (crop_coords[Stat.ITEM1][2] - 0.015))
                    )
                    add_text(frame, f'{states[player].item1}', item1_text_position, scale=1, thickness=3)

                    item2_text_position = (
                        round(frame.shape[1] * crop_coords[Stat.ITEM2][0]),
                        round(frame.shape[0] * (crop_coords[Stat.ITEM2][2] - 0.015))
                    )
                    add_text(frame, f'{player1_state.item2}', item2_text_position, scale=1, thickness=3)

                    for crop, coords in crop_coords.items():
                        cv2.rectangle(frame, (round(frame.shape[1] * coords[0]), round(frame.shape[0] * coords[2])),
                                      (round(frame.shape[1] * coords[1]), round(frame.shape[0] * coords[3])), (255, 0, 0), 2)
                cv2.imshow(f"Device {device_id}", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    stop_event.set()

        except Empty:
            continue


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


def main(_args: argparse.Namespace) -> None:
    # Create a process queue for frame processing
    process_queue = ProcessQueue(maxsize=_args.queue_size)

    # Create an event to signal process termination
    stop_event = Event()

    # Create and start capture processes
    capture_processes = []
    for i in range(_args.num_devices):
        source = _args.video_file if _args.video_file else i
        process = Process(target=capture_and_process,
                          args=(source, i, _args.resolution, _args.frame_skip, process_queue, _args.fps))
        process.start()
        capture_processes.append(process)

    match _args.sink:
        case SinkType.REDIS:
            sink = redis.Redis()
        case _:
            sink = None

    # Create and start frame processing processes
    processing_processes = []
    for _ in range(_args.threads):
        process = Process(target=process_frames,
                          args=(process_queue, stop_event, _args.display, _args.training_save_dir, None, None))
        process.start()
        processing_processes.append(process)

    # Create directory to save training crops if specified by user
    if _args.training_save_dir:
        os.makedirs(_args.training_save_dir, exist_ok=True)

    # Main loop
    try:
        while not stop_event.is_set():
            time.sleep(1)  # Sleep to reduce CPU usage of main thread
    except KeyboardInterrupt:
        print("Shutting down...")

    # Clean up
    stop_event.set()
    for process in capture_processes + processing_processes:
        process.join()

    if _args.display:
        cv2.destroyAllWindows()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mario Kart 8 Video Processing Pipeline")
    parser.add_argument("--video-file", type=str,
                        help="Path to the video file for emulation (optional)")
    parser.add_argument("--resolution", type=lambda s: tuple(map(int, s.split('x'))),
                        default=(640, 360), help="Downscale resolution (width x height)")
    parser.add_argument("--frame-skip", type=int, default=0,
                        help="Number of frames to skip between processed frames")
    parser.add_argument("--threads", type=int, default=2,
                        help="Number of processing threads")
    parser.add_argument("--queue-size", type=int, default=100,
                        help="Maximum size of the processing queue")
    parser.add_argument("--num-devices", type=int, default=2,
                        help="Number of capture devices or emulated streams")
    parser.add_argument("--fps", type=float, default=60.0,
                        help="Frames per second for video emulation (only used with --video-file)")
    parser.add_argument("--display", action="store_true",
                        help="Display processed frames (for debugging)")
    parser.add_argument('--sink', type=SinkType, default=SinkType.REDIS, choices=SinkType,
                        help="Choose the message broker to use for publishing the processed frames")
    parser.add_argument("--training-save-dir", type=str,
                        help="Directory to save training images (optional)")

    args = parser.parse_args()

    print(f"Running with settings:")
    print(f"Video file: {args.video_file if args.video_file else 'Not provided (using real devices)'}")
    print(f"Resolution: {args.resolution}")
    print(f"Frame skip: {args.frame_skip}")
    print(f"Threads: {args.threads}")
    print(f"Queue size: {args.queue_size}")
    print(f"Number of devices/streams: {args.num_devices}")
    print(f"FPS (for video file): {args.fps}")
    print(f"Display frames: {args.display}")
    print(f"Sink: {args.sink}")
    print(
        f"Save training images to directory: {args.training_save_dir if args.training_save_dir else 'Not provided (not saving training images)'}")

    main(args)
