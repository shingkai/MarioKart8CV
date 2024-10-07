import cv2
from cv2.typing import MatLike
import pytesseract

from state import Player, Stat, PlayerState

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


def extract_text(frame: MatLike, ) -> str:
    # Convert the image to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Run Tesseract OCR on the image
    text = pytesseract.image_to_string(gray)
    
    return text

def extract_player_state(frame: MatLike, player: Player) -> PlayerState:
    player_state = {stat: extract_text(frame[coords[1]:coords[1] + coords[3], coords[0]:coords[0] + coords[2]]) for stat, coords in text_aois[player].itmes()}
    print(player_state)
    return PlayerState.from_dict(player_state)
