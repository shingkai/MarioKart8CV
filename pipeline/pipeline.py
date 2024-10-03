import logging
from enum import Enum

import cv2
import argparse
from multiprocessing import Process, Queue as ProcessQueue, Event
from queue import Full, Empty
import time
from typing import Optional, Tuple, Union

from state import StateMessage, publish_to_redis, publish_to_rabbitmq, publish_to_kafka

import redis
import pika
from kafka import KafkaProducer


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
    RABBITMQ = 2
    KAFKA = 3


# Modify the process_frames function to use one of these methods
def process_frames(
        process_queue: ProcessQueue, stop_event: Event, display: bool,
        sink_type: SinkType = SinkType.REDIS,
        sink: Optional[redis.Redis | pika.channel.Channel | KafkaProducer] = None,
) -> None:
    while not stop_event.is_set():
        try:
            device_id, frame = process_queue.get(timeout=1)

            # Your friend's CV logic goes here
            # For now, we'll use dummy data
            frame_number = 0  # This should be extracted from the frame or tracked
            player1_state = {"position": 1, "item": "mushroom"}
            player2_state = {"position": 2, "item": "banana"}

            state_message = StateMessage(device_id, frame_number, player1_state, player2_state)

            # Choose one of the following based on your chosen method:
            match sink_type:
                case SinkType.REDIS:
                    publish_to_redis(sink, "mario_kart_states", state_message)
                case SinkType.RABBITMQ:
                    publish_to_rabbitmq(sink, "mario_kart_states", state_message)
                case SinkType.KAFKA:
                    publish_to_kafka(sink, "mario_kart_states", state_message)
                case _:
                    logging.info("state_message: %s", state_message.to_json())
            print(f"Processed and published frame {frame_number} from device {device_id}")

            if display:
                cv2.imshow(f"Device {device_id}", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    stop_event.set()

        except Empty:
            continue


def main(args: argparse.Namespace) -> None:
    # Create a process queue for frame processing
    process_queue = ProcessQueue(maxsize=args.queue_size)

    # Create an event to signal process termination
    stop_event = Event()

    # Create and start capture processes
    capture_processes = []
    for i in range(args.num_devices):
        source = args.video_file if args.video_file else i
        process = Process(target=capture_and_process,
                          args=(source, i, args.resolution, args.frame_skip, process_queue, args.fps))
        process.start()
        capture_processes.append(process)

    match args.sink:
        case SinkType.REDIS:
            sink = redis.Redis()
        case SinkType.RABBITMQ:
            connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
            channel = connection.channel()
            channel.queue_declare(queue='mario_kart_states')
            sink = connection.channel()
        case SinkType.KAFKA:
            sink = KafkaProducer(bootstrap_servers=['localhost:9092'])
        case _:
            sink = None

    # Create and start frame processing processes
    processing_processes = []
    for _ in range(args.threads):
        process = Process(target=process_frames, args=(process_queue, stop_event, args.display, args.sink, sink))
        process.start()
        processing_processes.append(process)

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

    if args.display:
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

    main(args)
