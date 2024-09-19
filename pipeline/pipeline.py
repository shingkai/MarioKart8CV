import cv2
import numpy as np
import argparse
from multiprocessing import Pool, cpu_count, Queue as ProcessQueue, Event
from queue import Full, Empty
from threading import Thread
import time
from typing import Optional, Tuple, Union


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

    if isinstance(source, int):  # Real device
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    # else:  # Video file
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
            process_queue.put((device_id, downscaled), block=False)
        except Full:
            print(f"Queue is full. Skipping frame from device {device_id}")

        if isinstance(source, str) and frame_time:  # Video file
            time.sleep(frame_time)  # Simulate real-time capture


def process_frame(frame_data: Tuple[int, cv2.typing.MatLike]) -> Tuple[int, str]:
    device_id, frame = frame_data
    # Stub for CV processing
    # Implement your CV logic here
    # time.sleep(0.0001)  # Simulate processing time
    return device_id, frame


def process_frames(process_queue: ProcessQueue, stop_event: Event, display: bool) -> None:
    while not stop_event.is_set():
        try:
            frame_data = process_queue.get(timeout=1)
            result = process_frame(frame_data)
            device_id, frame = result
            print(f"Processed frame {frame_data[0]} from device {device_id}")

            if display:
                # Display the frame
                cv2.imshow(f"Device {device_id}", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    stop_event.set()  # Set the stop event if 'q' is pressed
        except Empty:
            continue

def main(args: argparse.Namespace) -> None:
    # Create a process queue for frame processing
    process_queue = ProcessQueue(maxsize=args.queue_size)

    # Create an event to signal process termination
    stop_event = Event()

    # Create a pool of worker processes for CV tasks
    pool = Pool(processes=args.threads, initializer=process_frames, initargs=(process_queue, stop_event, args.display))

    # Create and start capture threads
    capture_threads = []
    for i in range(args.num_devices):
        source = args.video_file if args.video_file else i
        thread = Thread(target=capture_and_process,
                        args=(source, i, args.resolution, args.frame_skip, process_queue, args.fps))
        thread.start()
        capture_threads.append(thread)

    # Main loop
    try:
        while not stop_event.is_set():
            time.sleep(1)  # Sleep to reduce CPU usage of main thread
    except KeyboardInterrupt:
        print("Shutting down...")

    # Clean up
    stop_event.set()
    pool.close()
    pool.join()
    for thread in capture_threads:
        thread.join()

    cv2.destroyAllWindows()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mario Kart 8 Video Processing Pipeline")
    parser.add_argument("--video-file", type=str,
                        help="Path to the video file for emulation (optional)")
    parser.add_argument("--resolution", type=lambda s: tuple(map(int, s.split('x'))),
                        default=(640, 360), help="Downscale resolution (width x height)")
    parser.add_argument("--frame-skip", type=int, default=0,
                        help="Number of frames to skip between processed frames")
    parser.add_argument("--threads", type=int, default=cpu_count(),
                        help="Number of processing threads")
    parser.add_argument("--queue-size", type=int, default=100,
                        help="Maximum size of the processing queue")
    parser.add_argument("--num-devices", type=int, default=6,
                        help="Number of capture devices or emulated streams")
    parser.add_argument("--fps", type=float, default=60.0,
                        help="Frames per second for video emulation (only used with --video-file)")
    parser.add_argument("--display", action="store_true",
                        help="Display processed frames (for debugging)")

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

    main(args)
