import os.path
from abc import ABC, abstractmethod
import cv2
from cv2.typing import MatLike
import numpy as np


from mk8cv.data.state import Player, Stat, Item
from mk8cv.processing.aois import CROP_COORDS


class CoinClassifier(ABC):
    def __init__(self) -> None:
        self._model = None

    @abstractmethod
    def load(self, model_path: str) -> None:
        pass

    @abstractmethod
    def _predict(self, frame: MatLike) -> str:
        pass

    def extract_player_coins(self, frame: MatLike, player: Player) -> int:
        """Extracts the player's coins from the frame."""
        height, width, channels = frame.shape

        coin_coords = CROP_COORDS[player][Stat.COINS]
        coins = self._predict(frame[round(height * coin_coords[2]): round(height * coin_coords[3]), round(width * coin_coords[0]): round(width * coin_coords[1])])

        return coins
    

class CannyMaskCoinClassifier(CoinClassifier):
    def __init__(self):
        super().__init__()
        self._masks = None

    def load(self, model_path: str = "./templates/coins/edges/"):
        self._masks = self._load_templates(model_path, 'mask')

    def _predict(self, frame: MatLike):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        boosted = cv2.convertScaleAbs(gray, alpha=1.5, beta=0)
        canny = cv2.Canny(boosted, threshold1=50, threshold2=150)

        min_error = None
        best_mask = None
        for index, mask in self._masks.items():
            error = self._score_mask(canny, mask)

            if min_error == None or min_error > error:
                min_error = error
                best_mask = index

        return best_mask

    def _load_templates(self, template_dir: str, masks=False):
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
    
    def _score_mask(self, image, mask):
        height, width = image.shape[:2]
        masked_canny = cv2.bitwise_and(image, cv2.resize(mask, (width, height)))
        
        return np.sum(masked_canny)