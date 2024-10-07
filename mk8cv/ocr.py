import cv2
from cv2.typing import MatLike
import pytesseract

from state import Player, Stat, PlayerState, Item

# formatted as (x, y, width, height)
text_aois = {
    Player.P1 : {
        Stat.POSITION: (240, 300, 50, 50),
        Stat.COINS: (34, 330, 24, 20),
        Stat.LAP: (72, 330, 32, 20),
    },
    Player.P2 : {
        Stat.POSITION: (560, 300, 50, 50),
        Stat.COINS: (34, 330, 24, 20),
        Stat.LAP: (391, 330, 32, 20),
    },
}

TESSERACT_STATS = [Stat.POSITION, Stat.COINS, Stat.LAP]

def extract_text(frame: MatLike, config) -> str:
    # Convert the image to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, (0, 0), None, 4.0, 4.0)
    cv2.imshow('frame', gray)
    cv2.waitKey(0)

    # Run Tesseract OCR on the image
    text = pytesseract.image_to_string(gray, config=config)
    
    return text

def extract_text_lap_counter(frame: MatLike) -> str:
    return extract_text(frame, config='--oem 3 --psm 8 -c tessedit_char_whitelist=0123/')

def extract_text_coins(frame: MatLike) -> str:
    return extract_text(frame, config='--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789')

def extract_player_state(frame: MatLike, player: Player) -> PlayerState:
    player_state = {
        stat: extract_text(frame[coords[1]:coords[1] + coords[3], coords[0]:coords[0] + coords[2]]) for stat, coords in text_aois[player].items() if stat in TESSERACT_STATS
    }
    # player_state[Player.P1].update({Stat.ITEM1: Item.NONE, Stat.ITEM2: Item.NONE})
    # player_state[Player.P2].update({Stat.ITEM1: Item.NONE, Stat.ITEM2: Item.NONE})
    print(player_state)
    return PlayerState.from_dict(player_state)
