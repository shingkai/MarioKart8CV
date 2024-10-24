import os
from abc import abstractmethod, ABC
import logging

import cv2
from cv2.typing import MatLike

from mk8cv.data.state import Player


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
        """Extracts the player's items from the frame."""
        return self._predict(frame)

class SevenSegmentLapClassifier(LapClassifier):
    def __init__(self):
        super().__init__()

    def load(self, model_path: str = None):
        pass

    def _predict(self, frame: MatLike) -> tuple[int, int]:
        return -1, -1

        # result, visualization = self._recognize_seven_segment(frame)
        # # cv2.imshow('Visualization', cv2.resize(visualization, (0,0), fx=2.0, fy=2.0))
        # # cv2.waitKey(0)
        # return result

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
