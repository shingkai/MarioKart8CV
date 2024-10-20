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


