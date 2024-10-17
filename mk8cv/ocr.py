import os
from collections import Counter

import cv2
import numpy as np
from cv2.typing import MatLike
import pytesseract

from state import Player, Stat, PlayerState, Item

CROP_COORDS = {
    Player.P1 : {
        Stat.POSITION: (0.38, 0.47, 0.84, 0.97),
        Stat.COINS: (0.056, 0.09, 0.92, 0.965),
        Stat.LAP_NUM: (0.121, 0.135, 0.925, 0.9635),
        Stat.RACE_LAPS: (0.121, 0.161, 0.964, 0.999),
        Stat.ITEM1: (0.08, 0.164, 0.08, 0.23),
        Stat.ITEM2: (0.039, 0.082, 0.047, 0.13),
    },
    Player.P2 : {
        Stat.POSITION: (0.88, 0.97, 0.84, 0.97),
        Stat.COINS: (0.556, 0.59, 0.92, 0.965),
        Stat.LAP_NUM: (0.621, 0.635, 0.925, 0.9635),
        Stat.RACE_LAPS: (0.671, 0.711, 0.925, 0.964),
        Stat.ITEM1: (0.834, 0.918, 0.08, 0.23),
        Stat.ITEM2: (0.915, 0.958, 0.047, 0.13),
    }
}


TESSERACT_STATS = [Stat.POSITION, Stat.COINS, Stat.RACE_LAPS, Stat.LAP_NUM]

def load_templates(template_dir):
    templates = {}
    for filename in os.listdir(template_dir):
        if filename.endswith('.png'):
            if 'mask' in filename:
                continue
            number = filename.split('.')[0]
            template = cv2.imread(os.path.join(template_dir, filename), 0)
            templates[number] = template
    return templates

coin_templates = load_templates("templates/coins")
# lap_num_templates = load_templates("templates/lap_num")
# race_laps_templates = load_templates("templates/race_laps")

coin_mask = cv2.imread("templates/coins/mask_full.png", 0)
# lap_num_mask = cv2.imread("templates/lap_num/mask_full.png", 0)
# race_laps_mask = cv2.imread("templates/race_laps/mask_full.png", 0)

def match_template(image, template, mask, threshold=0.95):
    result = cv2.matchTemplate(image, template, cv2.TM_SQDIFF, mask=mask)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    # locations = np.where(result >= threshold)
    # return list(zip(*locations[::-1]))
    return min_val

def recognize_lap_num(image, templates):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # cv2.imshow('gray', gray)

    scores = {}
    for number, template in templates.items():
        score = match_template(gray, template, coin_mask)
        scores[number] = score

    print(scores)
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

    print(scores)
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

    print(scores)
    best = min(scores, key=scores.get)
    if best != 0:
        return best
    return None


# def extract_text(frame: MatLike, config) -> str:
#     # Convert the image to grayscale
#     # gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#     # gray = cv2.resize(gray, (0, 0), None, 4.0, 4.0)
#     # cv2.imshow('frame', gray)
#     # cv2.waitKey(0)
#
#     # Run Tesseract OCR on the image
#     # text = pytesseract.image_to_string(gray, config=config)
#     coins = recognize_coins(frame, templates)
#
#
#     return text
#
# def extract_text_lap_counter(frame: MatLike) -> str:
#     return extract_text(frame, config='--oem 3 --psm 8 -c tessedit_char_whitelist=0123/')

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
    return recognize_lap_num(frame, lap_num_templates)

def extract_text_race_laps(frame: MatLike) -> str:
    return recognize_race_laps(frame, race_laps_templates)

def extract_player_state(frame: MatLike, player: Player) -> PlayerState:

    coins_coords = CROP_COORDS[player][Stat.COINS]
    # lap_num_coords = CROP_COORDS[player][Stat.LAP_NUM]
    # race_laps_coords = CROP_COORDS[player][Stat.RACE_LAPS]
    height, width, channels = frame.shape
    coins = extract_text_coins(
        frame[round(height * coins_coords[2]): round(height * coins_coords[3]), round(width * coins_coords[0]): round(width * coins_coords[1])]
    )

    # lap_num = extract_text_lap_num(
    #     frame[round(height * lap_num_coords[2]): round(height * lap_num_coords[3]), round(width * lap_num_coords[0]): round(width * lap_num_coords[1])]
    # )
    #
    # race_laps = extract_text_race_laps(
    #     frame[round(height * race_laps_coords[2]): round(height * race_laps_coords[3]), round(width * race_laps_coords[0]): round(width * race_laps_coords[1])]
    # )

    player_state = {
        Stat.COINS: coins,
        Stat.LAP_NUM: 1,
        # Stat.LAP_NUM: lap_num,
        Stat.RACE_LAPS: 3,
        # Stat.RACE_LAPS: race_laps,
        Stat.POSITION: 1,
    }

    print(player_state)
    return PlayerState.from_dict(player_state)
