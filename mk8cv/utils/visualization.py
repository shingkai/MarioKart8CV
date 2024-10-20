from typing import Tuple

import cv2
from cv2.typing import MatLike

from mk8cv.data.state import Player, PlayerState, Stat
from mk8cv.processing.aois import CROP_COORDS


def add_text(frame: cv2.typing.MatLike, text: str, position: Tuple[int, int], color=(255, 0, 0), scale=2, thickness=5) -> None:
    cv2.putText(
        frame,
        text,
        position,
        cv2.FONT_HERSHEY_SIMPLEX,
        fontScale=scale,
        color=color,
        thickness=thickness
    )

def visualize(frame: MatLike, states: dict[Player, PlayerState], device_id: int, stop_event) -> None:
    height, width, channels = frame.shape
    for player in [Player.P1, Player.P2]:
        crop_coords = CROP_COORDS[player]
        coins_text_position = (
            round(frame.shape[1] * crop_coords[Stat.COINS][0]),
            round(frame.shape[0] * (crop_coords[Stat.COINS][2] - 0.015))
        )
        add_text(frame, f'{states[player].coins}', coins_text_position)

        lap_text_position = (
            round(frame.shape[1] * crop_coords[Stat.LAP_NUM][0]),
            round(frame.shape[0] * (crop_coords[Stat.LAP_NUM][2] - 0.015))
        )
        add_text(frame, f'{states[player].lap}/{states[player].race_laps}', lap_text_position,
                 scale=height / 1080,
                 thickness=int(3 * (height / 1080)))

        position_text_position = (
            round(frame.shape[1] * crop_coords[Stat.POSITION][0]),
            round(frame.shape[0] * (crop_coords[Stat.POSITION][2] - 0.015))
        )
        add_text(frame, f'{states[player].position}', position_text_position, scale=(height / 1080),
                 thickness=int(3 * (height / 1080)))

        item1_text_position = (
            round(frame.shape[1] * crop_coords[Stat.ITEM1][0]),
            round(frame.shape[0] * (crop_coords[Stat.ITEM1][2] - 0.015))
        )
        add_text(frame, f'{states[player].item1}', item1_text_position, scale=(height / 1080),
                 thickness=int(3 * (height / 1080)))

        item2_text_position = (
            round(frame.shape[1] * crop_coords[Stat.ITEM2][0]),
            round(frame.shape[0] * (crop_coords[Stat.ITEM2][2] - 0.015))
        )
        add_text(frame, f'{states[player].item2}', item2_text_position, scale=(height / 1080),
                 thickness=int(3 * (height / 1080)))

        for crop, coords in crop_coords.items():
            cv2.rectangle(frame,
                          (round(frame.shape[1] * coords[0]), round(frame.shape[0] * coords[2])),
                          (round(frame.shape[1] * coords[1]), round(frame.shape[0] * coords[3])),
                          (255, 0, 0), 2)
    cv2.imshow(f"Device {device_id}", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        stop_event.set()