import cv2
import pytest


@pytest.fixture
def video_capture(video_file):
    cap = cv2.VideoCapture(str(video_file))
    yield cap
    cap.release()

