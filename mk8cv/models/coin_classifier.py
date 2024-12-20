import functools
import operator
import os.path
from abc import ABC, abstractmethod
import cv2
from cv2.typing import MatLike
import numpy as np


from mk8cv.data.state import Player, Stat
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

    # def _preprocess_image(self, image):
    #     gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    #     image = cv2.resize(gray, (65 , 48))
    #     blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    #     # plt.figure()
    #     # plt.imshow(blurred)
    #     thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    #     # plt.figure()
    #     # plt.imshow(thresh)
    #     # boosted = cv2.convertScaleAbs(image, alpha=2, beta=-100)
    #     return thresh

    def _preprocess_image(self, image):
        # plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        # plt.title('Original Preprocess')
        image = cv2.resize(image, (65, 48))

        blurred = cv2.GaussianBlur(image, (5, 5), 0)
        # plt.imshow(blurred)
        # plt.title("blurred")

        # boosted = cv2.convertScaleAbs(blurred, alpha=1.5, beta=-100)
        # plt.imshow(boosted)
        # plt.title("boosted")

        gray = cv2.cvtColor(blurred, cv2.COLOR_BGR2GRAY)
        # plt.figure()
        # plt.imshow(cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR))
        # plt.title('gray')

        thresh = cv2.threshold(gray, 175, 255, cv2.THRESH_BINARY_INV)[1]
        # plt.figure()
        # plt.imshow(cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR))
        # plt.title("thresh")

        return thresh


    def _extract_segments(self, preprocessed_image, original_image):
        h, w = preprocessed_image.shape
        # cv2.imshow('preprocessed_image', preprocessed_image)
        # cv2.waitKey(0)

        # Define relative positions for each segment's check point
        # Format: (x1, y1, x2, y2) where 1 is for the first digit and 2 is for the second digit
        segment_points = [
            (0.185, 0.37),  # zero point
            (0.3, 0.4),  # one point
            (0.7, 0.2),  # Top
            (0.575, 0.35),  # Top-left
            (0.825, 0.35),  # Top-right
            (0.7, 0.5),  # Middle
            (0.55, 0.67),  # Bottom-left
            (0.785, 0.67),  # Bottom-right
            (0.675, 0.775)  # Bottom
        ]

        segments = []  # List to store segments for both digits
        # visualization = original_image.copy()
        visualization = cv2.cvtColor(preprocessed_image, cv2.COLOR_GRAY2BGR)

        # 120 / 255 -> set the threshold to at least 5/9 of the kernel (assuming 3x3 kernel)
        threshold = 120

        for i, (x, y) in enumerate(segment_points):
            # print(f"{preprocessed_image[int(h * y), int(w * x)]}")
            # segment_value = 1 if preprocessed_image[int(h * y), int(w * x)] > 250 else 0
            segment_area = preprocessed_image[int((h * y) - 1):int((h * y) + 1),
                           int((w * x) - 1):int((w * x) + 1)]
            segment_value = 1 if np.mean(segment_area) < threshold else 0
            cv2.circle(visualization, (int(x * w), int(y * h)), 1, (0, 255, 0) if segment_value else (255, 0, 0), thickness=-1)
            # print(f"{preprocessed_image[int(h * y), int(w * x)]}")

            segments.append(segment_value)

            # Visualization
            color = (0, 255, 0) if segment_value else (0, 0, 255)


        orange_segments = []
        for i, (x, y) in enumerate(list(segment_points)):
            image = cv2.resize(original_image, (65, 48))
            image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            lower_orange = np.array([5, 150, 150])
            upper_orange = np.array([25, 255, 255])

            segment_area = image[int((h * y) - 1):int((h * y) + 1),
                            int((w * x) - 1):int((w * x) + 1)]

            # check if the segment is orange
            segment_value = 1 if np.mean(cv2.inRange(segment_area, lower_orange, upper_orange)) > 0.5 else 0
            if segment_value:
                cv2.circle(visualization, (int(x * w), int(y * h)), 1, (0, 165, 255), thickness=-1)
            orange_segments.append(segment_value)

        is_ten = False
        if sum(orange_segments) >= 4:
            is_ten = True

        # return segments, visualization
        return segments, is_ten, preprocessed_image, visualization

    def _decode_segments(self, segments):
        segment_patterns = {
            #0  1  t  tl tr m  bl br b
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
        # result = segment_patterns.get(tuple(segments), -1)

        dists = [(np.abs(np.array(pattern) - np.array(segments)).sum(), digit) for pattern, digit in segment_patterns.items()]

        return min(dists, key=operator.itemgetter(0))[1]

    def _recognize_seven_segment(self, image):
        preprocessed = self._preprocess_image(image)
        segments, is_ten, preprocessed, visualization = self._extract_segments(preprocessed, image)

        # Convert preprocessed (grayscale) to BGR
        preprocessed_bgr = cv2.cvtColor(preprocessed, cv2.COLOR_GRAY2BGR)

        # Concatenate images horizontally
        debug_output = cv2.resize(cv2.hconcat([preprocessed_bgr, visualization]), (0, 0), fx=4.0, fy=4.0)

        # Display the concatenated image
        # cv2.imshow('Preprocessed | Visualization', debug_output)
        # cv2.waitKey(0)

        digit = 10 if is_ten else self._decode_segments(segments)
        recognized_number = digit

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