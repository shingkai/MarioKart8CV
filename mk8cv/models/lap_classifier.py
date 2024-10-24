import os
from abc import abstractmethod, ABC
import logging

import cv2
from cv2.typing import MatLike
import numpy as np

from mk8cv.data.state import Player, Stat
from mk8cv.processing.aois import CROP_COORDS


class LapClassifier(ABC):
    def __init__(self) -> None:
        self._model = None

    @abstractmethod
    def load(self, model_path: str = None) -> None:
        pass

    @abstractmethod
    def _predict(self, frame: MatLike) -> tuple[int, int]:
        pass

    def extract_laps(self, frame: MatLike, player: Player) -> tuple[int, int]:
        height, width, channels = frame.shape

        lap_num_coords = CROP_COORDS[player][Stat.LAP_NUM]
        race_laps_coords = CROP_COORDS[player][Stat.RACE_LAPS]

        lap_num = self._predict(frame=frame[round(height * lap_num_coords[2]): round(height * lap_num_coords[3]), round(width * lap_num_coords[0]): round(width * lap_num_coords[1])])
        race_laps = self._predict(frame=frame[round(height * race_laps_coords[2]): round(height * race_laps_coords[3]), round(width * race_laps_coords[0]): round(width * race_laps_coords[1])])

        return lap_num, race_laps

class SevenSegmentLapClassifier(LapClassifier):
    def __init__(self):
        super().__init__()

    def load(self, model_path: str = None):
        pass

    def _predict(self, frame: MatLike) -> tuple[int, int]:
        result, visualization = self._recognize_seven_segment(frame)
        return result

    def _preprocess_image(self, image):
        # plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        # plt.title('Original Preprocess')
        # image = cv2.resize(image, (65, 48))
        image = cv2.resize(image, (27, 42))

        blurred = cv2.GaussianBlur(image, (3, 3), 0)
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
            (0.47, 0.4), # one-top
            (0.43, 0.65), # one-bottom
            (0.5, 0.25),  # Top
            (0.3, 0.4),  # Top-left
            (0.7, 0.4),  # Top-right
            (0.45, 0.55),  # Middle
            (0.25, 0.65),  # Bottom-left
            (0.64, 0.65),  # Bottom-right
            (0.4, 0.8)  # Bottom
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

        # return segments, visualization
        return segments, preprocessed_image, visualization

    def _decode_segments(self, segments):
        segment_patterns = {
            #ot ob t  tl tr m  bl br b
            (0, 0, 1, 1, 1, 0, 1, 1, 1): 0,
            (1, 1, 0, 0, 0, 0, 0, 0, 0): 1,
            (0, 0, 1, 0, 1, 1, 1, 0, 1): 2,
            (0, 0, 1, 0, 1, 1, 0, 1, 1): 3,
            (0, 0, 0, 1, 1, 1, 0, 1, 0): 4,
            (0, 0, 1, 1, 0, 1, 0, 1, 1): 5,
            (0, 0, 1, 1, 0, 1, 1, 1, 1): 6,
            (0, 0, 1, 0, 1, 0, 0, 1, 0): 7,
            (0, 0, 1, 1, 1, 1, 1, 1, 1): 8,
            (0, 0, 1, 1, 1, 1, 0, 1, 1): 9,
        }
        result = segment_patterns.get(tuple(segments), -1)
        # print(f'result: {result}')
        return result

    def _recognize_seven_segment(self, image):
        preprocessed = self._preprocess_image(image)
        segments, preprocessed, visualization = self._extract_segments(preprocessed, image)

        # Convert preprocessed (grayscale) to BGR
        # preprocessed_bgr = cv2.cvtColor(preprocessed, cv2.COLOR_GRAY2BGR)

        # Concatenate images horizontally
        # debug_output = cv2.resize(cv2.hconcat([preprocessed_bgr, visualization]), (0, 0), fx=4.0, fy=4.0)

        # Display the concatenated image
        # cv2.imshow('Preprocessed | Visualization', debug_output)
        # cv2.waitKey(0)

        digit = self._decode_segments(segments)
        recognized_number = digit

        return recognized_number, visualization

class TemplateMatchingLapClassifier(LapClassifier):
    def __init__(self):
        super().__init__()
        self._lap_num_templates
        self._lap_num_masks
        self._race_laps_templates
        self._race_laps_masks

    def load(self, model_path: str = None) -> None:
        self._lap_num_templates = self._load_templates(os.path.join(model_path, "templates/lap_num"))
        self._lap_num_masks = self._load_templates(os.path.join(model_path, "templates/lap_num"), masks=True)
        self._race_laps_templates = self._load_templates(os.path.join(model_path, "templates/race_laps"))
        self._race_laps_masks = self._load_templates(os.path.join(model_path, "templates/race_laps"), masks=True)

    def _predict(self, frame: MatLike) -> tuple[int, int]:
        lap_nums = self._recognize_lap_num(frame, self._lap_num_templates, self._lap_num_masks)
        race_laps = self._recognize_race_laps(frame, self._race_laps_templates, self._race_laps_masks)

        return lap_nums, race_laps

    @staticmethod
    def _load_templates(template_dir, masks=False):
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
    
    @staticmethod
    def _match_template(image, template, mask, threshold=0.95):
        result = cv2.matchTemplate(image, template, cv2.TM_SQDIFF, mask=mask)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        # locations = np.where(result >= threshold)
        # return list(zip(*locations[::-1]))
        return min_val

    @staticmethod
    def _recognize_lap_num(image, templates, masks):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # cv2.imshow('gray', gray)

        scores = {}
        for number, template in templates.items():
            score = TemplateMatchingLapClassifier._match_template(gray, template, masks[number])
            scores[number] = score

        logging.debug(scores)
        best = min(scores, key=scores.get)
        if best != 0:
            return best
        return None

    def _recognize_race_laps(image, templates, masks):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # cv2.imshow('gray', gray)

        scores = {}
        for number, template in templates.items():
            score = TemplateMatchingLapClassifier._match_template(gray, template, masks[number])
            scores[number] = score

        logging.debug(scores)
        best = min(scores, key=scores.get)
        if best != 0:
            return best
        return None
