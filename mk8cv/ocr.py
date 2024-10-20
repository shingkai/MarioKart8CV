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
            # template = cv2.resize(cv2.imread(os.path.join(template_dir, filename), 0), (0, 0), fx=.2, fy=.2)
            templates[number] = template
    return templates

coin_templates = load_templates("templates/coins")
lap_num_templates = load_templates("templates/lap_num")
lap_num_masks = load_templates("templates/lap_num", masks=True)
# race_laps_templates = load_templates("templates/race_laps")
# race_laps_masks = load_templates("templates/race_laps", masks=True)
coin_mask = cv2.imread("templates/coins/mask_full.png", 0)
# coin_mask = cv2.resize(cv2.imread("templates/coins/mask_full.png", 0), (0, 0), fx=.2, fy=.2)
position_templates = load_templates("templates/position")
position_masks = load_templates("templates/position", masks=True)

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

# def recognize_race_laps(image, templates, masks):
#     gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
#     # cv2.imshow('gray', gray)
#
#     scores = {}
#     for number, template in templates.items():
#         score = match_template(gray, template, masks[number])
#         scores[number] = score
#
#     logging.debug(scores)
#     best = min(scores, key=scores.get)
#     if best != 0:
#         return best
#     return None

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

def recognize_position(image, templates, masks):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    scores = {}
    for number, template in templates.items():
        score = match_template(gray, template, masks[number])
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

def extract_text_position(frame: MatLike) -> str:
    return recognize_position(frame, position_templates, position_masks)

# def extract_text_race_laps(frame: MatLike) -> str:
#     return recognize_race_laps(frame, race_laps_templates, race_laps_masks)

def extract_coins(frame: MatLike, player: Player) -> int:
    coins_coords = CROP_COORDS[player][Stat.COINS]
    height, width, channels = frame.shape
    return int(extract_text_coins(
        frame[round(height * coins_coords[2]): round(height * coins_coords[3]), round(width * coins_coords[0]): round(width * coins_coords[1])]
    ))

def extract_laps(frame: MatLike, player: Player) -> tuple[int, int]:
    lap_num_coords = CROP_COORDS[player][Stat.LAP_NUM]
    # race_laps_coords = CROP_COORDS[player][Stat.RACE_LAPS]
    height, width, channels = frame.shape
    return (int(extract_text_lap_num(
        frame[round(height * lap_num_coords[2]): round(height * lap_num_coords[3]), round(width * lap_num_coords[0]): round(width * lap_num_coords[1])]
    )), 3)
    #         int(extract_text_race_laps(
    #     frame[round(height * race_laps_coords[2]): round(height * race_laps_coords[3]), round(width * race_laps_coords[0]): round(width * race_laps_coords[1])]
    # )))

def extract_position(frame: MatLike, player: Player) -> int:
    position_coords = CROP_COORDS[player][Stat.POSITION]
    height, width, channels = frame.shape
    return int(extract_text_position(
        frame[round(height * position_coords[2]): round(height * position_coords[3]), round(width * position_coords[0]): round(width * position_coords[1])]
    ))