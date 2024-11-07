import logging
import multiprocessing
import os
import cv2
import argparse
from multiprocessing import Process, Event
import time


import redis

from mk8cv.capture.capture import capture_and_process
from mk8cv.data.state import Stat
from mk8cv.processing.frame_processor import process_frames
from mk8cv.sinks.sink import SinkType


def main(_args: argparse.Namespace) -> None:
    # Create a process queue for frame processing
    m = multiprocessing.Manager()
    process_queue = m.Queue(maxsize=_args.queue_size)

    # Create an event to signal process termination
    stop_capture_event = Event()
    stop_process_event = Event()

    # Create and start capture processes
    capture_processes = []
    for i in range(_args.num_devices):
        source = _args.video_file if _args.video_file else i
        process = Process(target=capture_and_process,
                          args=(source, i, _args.resolution, _args.frame_skip, process_queue, stop_capture_event, _args.fps))
        process.start()
        capture_processes.append(process)

    # Create and start frame processing processes
    processing_processes = []
    for _ in range(_args.threads):
        process = Process(target=process_frames,
                          args=(
                          process_queue, stop_process_event, _args.race_id, _args.display, _args.training_save_dir, _args.write_csv, _args.sink, _args.extract))
        process.start()
        processing_processes.append(process)

    # Create directory to save training crops if specified by user
    if _args.training_save_dir:
        os.makedirs(_args.training_save_dir, exist_ok=True)

    # Main loop
    try:
        while not (stop_process_event.is_set() and stop_capture_event.is_set()):
            time.sleep(1)  # Sleep to reduce CPU usage of main thread

            # Check if all capture processes have finished
            if not stop_capture_event.is_set():
                if all(not p.is_alive() for p in capture_processes):
                    logging.info("All capture processes have finished")
                    stop_capture_event.set()
            if not stop_process_event.is_set():
                if all(not p.is_alive() for p in processing_processes):
                    logging.info("All processing processes have finished")
                    stop_process_event.set()

    except KeyboardInterrupt:
        logging.info("Shutting down...")

    # Clean up
    stop_capture_event.set()
    stop_process_event.set()
    for process in capture_processes + processing_processes:
        process.join()

    if _args.display:
        cv2.destroyAllWindows()

def parse_enum(enum_class):
    def parse(value):
        try:
            return enum_class(value)
        except ValueError:
            raise argparse.ArgumentTypeError(f"Invalid {enum_class.__name__} value: {value}")
    return parse

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
    parser.add_argument('--sink', type=lambda sink: SinkType[sink], default=SinkType.REDIS, choices=list(SinkType),
                        help="Choose the message broker to use for publishing the processed frames")
    parser.add_argument("--training-save-dir", type=str,
                        help="Directory to save training images (optional)")
    parser.add_argument("--extract", type=parse_enum(Stat), nargs='*', choices=list(Stat), default=list(Stat),
                        help="Skip extracting player state and items")
    parser.add_argument("--write-csv", action='store_true',
                        help="enable/disable writing extracted stats to csv")
    parser.add_argument("--race-id", type=int,
                        help="manually specify a race_id (defaults to random int)")

    logging.getLogger().setLevel(logging.INFO)
    args = parser.parse_args()

    if args.extract is not None and args.extract:
        import torch
        torch.multiprocessing.set_start_method('spawn')

    logging.info(f"Running with settings:")
    logging.info(f"Video file: {args.video_file if args.video_file else 'Not provided (using real devices)'}")
    logging.info(f"Resolution: {args.resolution}")
    logging.info(f"Frame skip: {args.frame_skip}")
    logging.info(f"Threads: {args.threads}")
    logging.info(f"Queue size: {args.queue_size}")
    logging.info(f"Number of devices/streams: {args.num_devices}")
    logging.info(f"FPS (for video file): {args.fps}")
    logging.info(f"Display frames: {args.display}")
    logging.info(f"Sink: {args.sink}")
    logging.info(f"Extracting: {args.extract}")
    logging.info(f"CSV writing: {args.write_csv}")
    logging.info(f"Race ID: {args.race_id}")
    logging.info(
        f"Save training images to directory: {args.training_save_dir if args.training_save_dir else 'Not provided (not saving training images)'}")

    main(args)
