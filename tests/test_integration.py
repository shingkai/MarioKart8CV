



def test_extractions(video_capture):
    # Test a few specific frames to ensure correct classification
        # video_capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    stopped = False

    while not stopped:
        ret, frame = video_capture.read()

    frame_annotation = annotations.get(str(frame_number))
    assert frame_annotation, f"No annotation found for frame {frame_number}"

    for player in Player:
        expected_item1 = Item(frame_annotation[player.name]["item1"])
        expected_item2 = Item(frame_annotation[player.name]["item2"])

        predicted_item1, predicted_item2 = extract_player_items(frame, player)

        assert predicted_item1 == expected_item1, f"Frame {frame_number}, Player {player.name}: Item 1 mismatch. Expected {expected_item1}, got {predicted_item1}"
        assert predicted_item2 == expected_item2, f"Frame {frame_number}, Player {player.name}: Item 2 mismatch. Expected {expected_item2}, got {predicted_item2}"