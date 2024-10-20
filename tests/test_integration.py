import csv

import cv2
import pytest

from mk8cv.data.state import Stat, StateMessage, PlayerState, Item
from mk8cv.models.coin_classifier import SevenSegmentCoinClassifier
from mk8cv.models.item_classifier import MobileNetV3ItemClassifier
from mk8cv.models.lap_classifier import SevenSegmentLapClassifier
from mk8cv.models.position_classifier import CannyMaskPositionClassifier
from mk8cv.processing.frame_processor import process_frame



class TestIntegration:

    @pytest.mark.parametrize('video_file', ['../test.mp4'])
    def test_extractions(self, video_capture, video_file):
        video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        stopped = False

        coin_model = SevenSegmentCoinClassifier()
        coin_model.load()
        item_model = MobileNetV3ItemClassifier()
        item_model.load()
        position_model = CannyMaskPositionClassifier()
        position_model.load()
        lap_model = SevenSegmentLapClassifier()
        lap_model.load()

        expected = []
        with open('../item_annotations.csv', 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                as_message = StateMessage(0, int(row['frame_number']), 0, PlayerState(
                    position=int(row['player1_position']),
                    item1=Item[row['player1_item1'].upper().replace(' ', '_')],
                    item2=Item[row['player1_item2'].upper().replace(' ', '_')],
                    coins=int(row['player1_coins']),
                    lap_num=int(row['player1_lap_num']),
                    race_laps=int(row['player1_race_laps'])
                ), PlayerState(
                    position=int(row['player2_position']),
                    item1=Item[row['player2_item1'].upper().replace(' ', '_')],
                    item2=Item[row['player2_item2'].upper().replace(' ', '_')],
                    coins=int(row['player2_coins']),
                    lap_num=int(row['player2_lap_num']),
                    race_laps=int(row['player2_race_laps'])
                ))
                expected.append(as_message)

        assert expected, "No expected messages found in test_annotations.json"

        count = 1
        wrong_frames = []
        while not stopped:
            ret, frame = video_capture.read()
            if not ret:
                stopped = True
            else:
                output = process_frame(0, count, frame, list(Stat), coin_model, item_model, position_model, lap_model)
                if output != expected[count - 1]:
                    wrong_frames.append((count, output, expected[count - 1]))

        assert len(wrong_frames) == 0, f"{len(wrong_frames)} frames had incorrect StateMessages: {wrong_frames[:5]}"




    # frame_annotation = annotations.get(str(frame_number))
    # assert frame_annotation, f"No annotation found for frame {frame_number}"
    #
    # for player in Player:
    #     expected_item1 = Item(frame_annotation[player.name]["item1"])
    #     expected_item2 = Item(frame_annotation[player.name]["item2"])
    #
    #     predicted_item1, predicted_item2 = extract_player_items(frame, player)
    #
    #     assert predicted_item1 == expected_item1, f"Frame {frame_number}, Player {player.name}: Item 1 mismatch. Expected {expected_item1}, got {predicted_item1}"
    #     assert predicted_item2 == expected_item2, f"Frame {frame_number}, Player {player.name}: Item 2 mismatch. Expected {expected_item2}, got {predicted_item2}"