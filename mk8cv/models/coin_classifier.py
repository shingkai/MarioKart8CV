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
    def load(self, model_path: str = None) -> None:
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

class SevenSegmentCoinClassifier(CoinClassifier):

    def __init__(self):
        super().__init__()

    def load(self, model_path: str = None):
        pass

    def _predict(self, frame: MatLike):
        result, visualization = self._recognize_seven_segment(frame)
        # cv2.imshow('Visualization', cv2.resize(visualization, (0,0), fx=2.0, fy=2.0))
        # cv2.waitKey(0)
        return result

    def _preprocess_image(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        image = cv2.resize(gray, (65 , 48))
        # blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        # plt.figure()
        # plt.imshow(blurred)
        # thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
        # plt.figure()
        # plt.imshow(thresh)
        boosted = cv2.convertScaleAbs(image, alpha=2, beta=-100)
        return boosted

    def _extract_segments(self, preprocessed_image, original_image):
        h, w = preprocessed_image.shape

        first_digit_points = [
            (0.125, 0.3),  # zero point
            (0.45, 0.3),  # one point
        ]
        # Define relative positions for each segment's check point
        # Format: (x1, y1, x2, y2) where 1 is for the first digit and 2 is for the second digit
        segment_points = [
            (0.18, 0.4),  # zero point
            (0.3, 0.4),  # one point
            (0.7, 0.2),  # Top
            (0.575, 0.35),  # Top-left
            (0.825, 0.35),  # Top-right
            (0.7, 0.5),  # Middle
            (0.55, 0.67),  # Bottom-left
            (0.775, 0.67),  # Bottom-right
            (0.675, 0.775)  # Bottom
        ]

        segments = []  # List to store segments for both digits
        visualization = original_image.copy()

        for i, (x, y) in enumerate(segment_points):
            point1 = (int(x * w), int(y * h))
            # print(f"{preprocessed_image[int(h * y), int(w * x)]}")
            segment_value = 1 if preprocessed_image[int(h * y), int(w * x)] > 250 else 0
            cv2.circle(preprocessed_image, (int(x * w), int(y * h)), 1, (0, 0, 0), thickness=-1)
            # print(f"{preprocessed_image[int(h * y), int(w * x)]}")

            segments.append(segment_value)

            # Visualization
            color = (0, 255, 0) if segment_value else (0, 0, 255)

        # return segments, visualization
        return segments, preprocessed_image

    def _decode_segments(self, segments):
        segment_patterns = {
            #    0  1  t  tl tr m  bl br b
            (1, 0, 1, 1, 1, 0, 1, 1, 1): 0,
            (1, 0, 0, 0, 1, 0, 0, 1, 0): 1,
            (1, 0, 1, 0, 1, 1, 1, 0, 1): 2,
            (1, 0, 1, 0, 1, 1, 0, 1, 1): 3,
            (1, 0, 0, 1, 1, 1, 0, 1, 0): 4,
            (1, 0, 1, 1, 0, 1, 0, 1, 1): 5,
            (1, 0, 1, 1, 0, 1, 1, 1, 1): 6,
            (1, 0, 1, 0, 1, 0, 0, 1, 0): 7,
            (1, 0, 1, 1, 1, 1, 1, 1, 1): 8,
            (1, 0, 1, 1, 1, 1, 0, 1, 1): 9,
        }
        result = segment_patterns.get(tuple(segments), -1)
        # print(f'result: {result}')
        if result == -1 and segments[:2] == [0, 1]:
            return 10
        else:
            return result

    def _recognize_seven_segment(self, image):
        preprocessed = self._preprocess_image(image)
        segments, visualization = self._extract_segments(preprocessed, image)
        # print(segments)
        digit = self._decode_segments(segments)
        recognized_number = str(digit)

        return recognized_number, visualization


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