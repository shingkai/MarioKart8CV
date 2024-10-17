import logging
import os

import cv2
import numpy as np
from cv2.typing import MatLike

from aois import CROP_COORDS
from state import Player, Stat, PlayerState


TESSERACT_STATS = [Stat.POSITION, Stat.COINS, Stat.RACE_LAPS, Stat.LAP_NUM]

def load_templates(template_dir, masks=False):
    templates = {}
    for filename in os.listdir(template_dir):
        if filename.endswith('.png'):
            if masks and not filename.endswith('_mask.png'):
                continue
            elif not masks and (filename.endswith('_mask.png') or 'mask' in filename):
                continue
            number = filename.split('.')[0]
            if masks:
                number = number.split('_')[0]
            template = cv2.imread(os.path.join(template_dir, filename), 0)
            templates[number] = template
    return templates

coin_templates = load_templates("templates/coins")
lap_num_templates = load_templates("templates/lap_num")
lap_num_masks = load_templates("templates/lap_num", masks=True)
# race_laps_templates = load_templates("templates/race_laps", mask_suffix='')
# race_laps_masks = load_templates("templates/race_laps", mask_suffix='_mask.png')
coin_mask = cv2.imread("templates/coins/mask_full.png", 0)

def match_template(image, template, mask, threshold=0.95):
    result = cv2.matchTemplate(image, template, cv2.TM_SQDIFF, mask=mask)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    # locations = np.where(result >= threshold)
    # return list(zip(*locations[::-1]))
    return min_val

def recognize_lap_num(image, templates, masks):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # cv2.imshow('gray', gray)

    scores = {}
    for number, template in templates.items():
        score = match_template(gray, template, masks[number])
        scores[number] = score

    logging.debug(scores)
    best = min(scores, key=scores.get)
    if best != 0:
        return best
    return None

def recognize_race_laps(image, templates):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # cv2.imshow('gray', gray)

    scores = {}
    for number, template in templates.items():
        score = match_template(gray, template, coin_mask)
        scores[number] = score

    logging.debug(scores)
    best = min(scores, key=scores.get)
    if best != 0:
        return best
    return None

def recognize_coins(image, templates):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # cv2.imshow('gray', gray)

    scores = {}
    for number, template in templates.items():
        score = match_template(gray, template, coin_mask)
        scores[number] = score

    logging.debug(scores)
    best = min(scores, key=scores.get)
    if best != 0:
        return best
    return None

def preprocess_image(image_path):
    # Read the image
    img = cv2.imread(image_path)

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply threshold to get white regions
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

    # Perform morphological operations to clean up the image
    kernel = np.ones((3, 3), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    return thresh

def extract_text_coins(frame: MatLike) -> str:
    return recognize_coins(frame, coin_templates)

def extract_text_lap_num(frame: MatLike) -> str:
    return recognize_lap_num(frame, lap_num_templates, lap_num_masks)

# def extract_text_race_laps(frame: MatLike) -> str:
#     return recognize_race_laps(frame, race_laps_templates)

def extract_player_state(frame: MatLike, player: Player) -> PlayerState:

    coins_coords = CROP_COORDS[player][Stat.COINS]
    lap_num_coords = CROP_COORDS[player][Stat.LAP_NUM]
    # race_laps_coords = CROP_COORDS[player][Stat.RACE_LAPS]
    height, width, channels = frame.shape
    coins = extract_text_coins(
        frame[round(height * coins_coords[2]): round(height * coins_coords[3]), round(width * coins_coords[0]): round(width * coins_coords[1])]
    )

    lap_num = extract_text_lap_num(
        frame[round(height * lap_num_coords[2]): round(height * lap_num_coords[3]), round(width * lap_num_coords[0]): round(width * lap_num_coords[1])]
    )
    #
    # race_laps = extract_text_race_laps(
    #     frame[round(height * race_laps_coords[2]): round(height * race_laps_coords[3]), round(width * race_laps_coords[0]): round(width * race_laps_coords[1])]
    # )

    player_state = {
        Stat.COINS: coins,
        Stat.LAP_NUM: lap_num,
        Stat.RACE_LAPS: 3,
        # Stat.RACE_LAPS: race_laps,
        Stat.POSITION: 1,
    }

    logging.debug(player_state)
    return PlayerState.from_dict(player_state)
