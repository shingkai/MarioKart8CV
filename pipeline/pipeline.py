import cv2
import numpy as np
import argparse
from multiprocessing import Pool, cpu_count
from queue import Queue
from threading import Thread


def capture_and_downscale(device_id, downscale_resolution, frame_skip):
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

        # Here you would send the downscaled frame to the processing queue
        # process_queue.put((device_id, downscaled))


def process_frame(frame_data):
    device_id, frame = frame_data
    # Stub for CV processing
    # Implement your CV logic here
    return device_id, "Processed data"


def main(_args: argparse.Namespace):
    num_devices = 6  # Number of HDMI inputs

    # Create a pool of worker processes for CV tasks
    pool = Pool(processes=_args.threads)

    # Create and start capture threads
    capture_threads = []
    for i in range(num_devices):
        thread = Thread(target=capture_and_downscale, args=(i, _args.resolution, _args.frame_skip))
        thread.start()
        capture_threads.append(thread)

    # Main processing loop
    try:
        while True:
            # In a real implementation, you would get frames from a queue here
            # frame = process_queue.get()

            # Process frames asynchronously
            # result = pool.apply_async(process_frame, (frame,))

            # Handle results (e.g., update leaderboards, stats)
            # processed_data = result.get()
            pass

    except KeyboardInterrupt:
        print("Shutting down...")

    # Clean up
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

    args = parser.parse_args()

    print(f"Running with settings:")
    print(f"Resolution: {args.resolution}")
    print(f"Frame skip: {args.frame_skip}")
    print(f"Threads: {args.threads}")

    main(args)
