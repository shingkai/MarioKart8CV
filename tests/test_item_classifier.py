import pytest
import cv2
import json
from pathlib import Path
from mk8cv.item_classifier import extract_player_items
from mk8cv.state import Item, Player

# Assuming you have a JSON file with frame-by-frame annotations
ANNOTATIONS_FILE = Path("tests/data/item_annotations.json")
VIDEO_FILE = Path("tests/data/test_video.mp4")

def load_annotations(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

@pytest.fixture(scope="module")
def video_capture():
    cap = cv2.VideoCapture(str(VIDEO_FILE))
    yield cap
    cap.release()

@pytest.fixture(scope="module")
def annotations():
    return load_annotations(ANNOTATIONS_FILE)

def test_item_classification(video_capture, annotations):
    frame_number = 0
    correct_predictions = 0
    total_predictions = 0

    while True:
        ret, frame = video_capture.read()
        if not ret:
            break

        frame_annotation = annotations.get(str(frame_number))
        if frame_annotation:
            for player in Player:
                expected_item1 = Item(frame_annotation[player.name]["item1"])
                expected_item2 = Item(frame_annotation[player.name]["item2"])

                predicted_item1, predicted_item2 = extract_player_items(frame, player)

                if predicted_item1 == expected_item1:
                    correct_predictions += 1
                total_predictions += 1

                if predicted_item2 == expected_item2:
                    correct_predictions += 1
                total_predictions += 1

        frame_number += 1

    accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0
    print(f"Item Classification Accuracy: {accuracy:.2%}")
    assert accuracy > 0.90, f"Accuracy {accuracy:.2%} is below the expected threshold of 90%"

def test_specific_frames(video_capture, annotations):
    # Test a few specific frames to ensure correct classification
    test_frames = [0, 100, 500, 1000]  # Add more frame numbers as needed

    for frame_number in test_frames:
        video_capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = video_capture.read()
        assert ret, f"Could not read frame {frame_number}"

        frame_annotation = annotations.get(str(frame_number))
        assert frame_annotation, f"No annotation found for frame {frame_number}"

        for player in Player:
            expected_item1 = Item(frame_annotation[player.name]["item1"])
            expected_item2 = Item(frame_annotation[player.name]["item2"])

            predicted_item1, predicted_item2 = extract_player_items(frame, player)

            assert predicted_item1 == expected_item1, f"Frame {frame_number}, Player {player.name}: Item 1 mismatch. Expected {expected_item1}, got {predicted_item1}"
            assert predicted_item2 == expected_item2, f"Frame {frame_number}, Player {player.name}: Item 2 mismatch. Expected {expected_item2}, got {predicted_item2}"

if __name__ == "__main__":
    pytest.main([__file__])