from abc import ABC, abstractmethod
import logging
import os

import torch
import torch.nn as nn
from torchvision import models, transforms
import cv2
from cv2.typing import MatLike
import numpy as np
import matplotlib.pyplot as plt

from mk8cv.data.state import Player, Stat
from mk8cv.processing.aois import CROP_COORDS


classes = ["00","01","02","03","04","05","06","07","08","09","10","11","12"]


class PositionClassifier(ABC):
    def __init__(self) -> None:
        self._model = None
        # Check if GPU is available (either cuda for nvidia or mps for apple silicon)
        self._device = torch.device("cuda:0" if torch.cuda.is_available() else torch.device("mps") if torch.backends.mps.is_available() else  torch.device("cpu"))
        self._classes = classes

    @abstractmethod
    def load(self, model_path: str) -> None:
        pass

    @abstractmethod
    def _predict(self, frame: MatLike) -> str:
        pass

    def extract_player_position(self, frame: MatLike, player: Player) -> int:
        """Extracts the player's items from the frame."""
        height, width, channels = frame.shape

        position_coords = CROP_COORDS[player][Stat.POSITION]
        position = self._predict(frame[round(height * position_coords[2]): round(height * position_coords[3]), round(width * position_coords[0]): round(width * position_coords[1])])

        return int(position)


class MobileNetV3PositionClassifier(PositionClassifier):
    def __init__(self):
        super().__init__()

    def load(self, model_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'position_classifier_mobilenetv3.pth')):
        self._model = models.mobilenet_v3_large(weights=None)
        num_classes = len(self._classes)
        self._model.classifier[3] = nn.Linear(self._model.classifier[3].in_features, num_classes)
        self._model.load_state_dict(torch.load(model_path, map_location=self._device, weights_only=True))
        self._model = self._model.to(self._device)
        self._model.eval()
        return self._model

    def _predict(self, frame: MatLike):
        img_width, img_height = 96, 96
        preprocess = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((img_width, img_height)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])

        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = preprocess(image).unsqueeze(0).to(self._device)

        with torch.no_grad():
            output = self._model(image)
            _, predicted = torch.max(output, 1)

        predicted_class = classes[predicted.item()]
        return predicted_class


class TemplatePositionClassifier(PositionClassifier):
    def __init__(self):
        super().__init__()
        self._templates = None
        self._masks = None

    def load(self, model_path: str = "./templates/position"):
        self._templates = self._load_templates(model_path)
        self._masks = self._load_templates(model_path, 'mask')

    def _predict(self, frame: MatLike):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        scores = {}
        for number, template in self._templates.items():
            score = self._match_template(gray, template, self._masks[number])
            scores[number] = score

        logging.debug(scores)
        best = min(scores, key=scores.get)
        if best != 0:
            return best
        return None

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

    def _match_template(self, image, template, mask, threshold=0.95):
        result = cv2.matchTemplate(image, template, cv2.TM_SQDIFF, mask=mask)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        return min_val
    

class CannyMaskPositionClassifier(PositionClassifier):
    def __init__(self, threshold = 10000):
        super().__init__()
        self._masks = None
        self._threshold = threshold


    def load(self, model_path: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../templates/position/edges/')):
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

        return best_mask if min_error < self._threshold else 0

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