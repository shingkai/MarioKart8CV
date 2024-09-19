import cv2
import numpy as np
import argparse
from multiprocessing import Pool, cpu_count, Queue as ProcessQueue, Event
from queue import Full, Empty
from threading import Thread
import time


def capture_and_downscale(
        device_id: int,
        downscale_resolution: tuple[int, int],
        frame_skip: int,
        process_queue: ProcessQueue
) -> None:
    cap = cv2.VideoCapture(device_id)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        if frame_count % (frame_skip + 1) != 0:
            continue

        # Downscale to specified resolution
        downscaled = cv2.resize(frame, downscale_resolution)

        # Try to put the frame in the queue, if it's full, skip this frame
        try:
            process_queue.put((device_id, downscaled), block=False)
        except Full:
            print(f"Queue is full. Skipping frame from device {device_id}")


def process_frame(frame_data: tuple[int, cv2.typing.MatLike]) -> tuple[int, str]:
    device_id, frame = frame_data
    # Stub for CV processing
    # Implement your CV logic here
    time.sleep(0.01)  # Simulate processing time
    return device_id, "Processed data"


def process_frames(process_queue: ProcessQueue, stop_event: Event) -> None:
    while not stop_event.is_set():
        try:
            frame_data = process_queue.get(timeout=1)
            result = process_frame(frame_data)
            # Here you would handle the processed result
            # e.g., update leaderboards, stats, etc.
            print(f"Processed frame from device {result[0]}")
        except Empty:
            continue


def main(_args: argparse.Namespace) -> None:
    num_devices = 6  # Number of HDMI inputs

    # Create a process queue for frame processing
    process_queue = ProcessQueue(maxsize=_args.queue_size)

    # Create an event to signal process termination
    stop_event = Event()

    # Create a pool of worker processes for CV tasks
    pool = Pool(processes=_args.threads, initializer=process_frames, initargs=(process_queue, stop_event))

    # Create and start capture threads
    capture_threads = []
    for i in range(num_devices):
        thread = Thread(target=capture_and_downscale, args=(i, _args.resolution, _args.frame_skip, process_queue))
        thread.start()
        capture_threads.append(thread)

    # Main loop
    try:
        while True:
            time.sleep(1)  # Sleep to reduce CPU usage of main thread
    except KeyboardInterrupt:
        print("Shutting down...")

    # Clean up
    stop_event.set()
    pool.close()
    pool.join()
    for thread in capture_threads:
        thread.join()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mario Kart 8 Video Processing Pipeline")
    parser.add_argument("--resolution", type=lambda s: tuple(map(int, s.split('x'))),
                        default=(640, 360), help="Downscale resolution (width x height)")
    parser.add_argument("--frame-skip", type=int, default=0,
                        help="Number of frames to skip between processed frames")
    parser.add_argument("--threads", type=int, default=cpu_count(),
                        help="Number of processing threads")
    parser.add_argument("--queue-size", type=int, default=100,
                        help="Maximum size of the processing queue")

    parsed_args = parser.parse_args()

    print(f"Running with settings:")
    print(f"Resolution: {parsed_args.resolution}")
    print(f"Frame skip: {parsed_args.frame_skip}")
    print(f"Threads: {parsed_args.threads}")
    print(f"Queue size: {parsed_args.queue_size}")

    main(parsed_args)
