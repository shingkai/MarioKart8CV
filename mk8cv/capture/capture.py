import logging
import cv2
from multiprocessing import Event, Queue
from queue import Full
import time
from typing import Optional, Tuple, Union


def capture_and_process(
        source: Union[int, str],
        device_id: int,
        downscale_resolution: Tuple[int, int],
        frame_skip: int,
        process_queue: Queue,
        stop_event: Event,
        fps: Optional[float] = None
) -> None:
    logging.getLogger().setLevel(logging.INFO)
    logging.info(f"Starting capture process for device {device_id}...")

    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        logging.error(f"Error opening video source: {source}")
        stop_event.set()
        return

    frame_time = None

    if isinstance(source, int):  # Real device
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    else:  # Video file
        frame_time = 1 / fps if fps else 0

    frame_count = 0
    start_time = time.time()
    frames_processed = 0

    while not stop_event.is_set():
        ret, frame = cap.read()
        if not ret:
            if isinstance(source, str):  # Video file
                logging.info(f"End of video file reached for device {device_id}")
                stop_event.set()
                break
            else:
                stop_event.set()
                break

        frame_count += 1
        if frame_count % (frame_skip + 1) != 0:
            continue

        # Downscale to specified resolution
        downscaled = cv2.resize(frame, downscale_resolution)

        # Try to put the frame in the queue, if it's full, skip this frame
        try:
            process_queue.put((device_id, frame_count, downscaled), block=False)
            frames_processed += 1

            # Calculate and log FPS every second
            elapsed_time = time.time() - start_time
            if elapsed_time >= 1.0:
                actual_fps = frames_processed / elapsed_time
                logging.info(f"Device {device_id}: Actual FPS = {actual_fps:.2f}")
                frames_processed = 0
                start_time = time.time()

        except Full:
            sleep = 1
            logging.warning(f"Queue is full. Backing off for device {device_id} for {sleep} seconds")
            while process_queue.full():
                time.sleep(1)
                sleep *= 2
        if isinstance(source, str) and frame_time:  # Video file
            time.sleep(frame_time)  # Simulate real-time capture

    cap.release()
    logging.info(f"Capture process for device {device_id} finished")