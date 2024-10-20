from abc import ABC, abstractmethod
import torch
import torch.nn as nn
from torchvision import models, transforms
import cv2
from cv2.typing import MatLike

from state import Player, Stat, PlayerState
from aois import CROP_COORDS


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

    def load(self, model_path='./models/position_classifier_mobilenetv3.pth'):
        self._model = models.mobilenet_v3_large(pretrained=False)
        num_classes = len(self._classes)
        self._model.classifier[3] = nn.Linear(self._model.classifier[3].in_features, num_classes)
        self._model.load_state_dict(torch.load(model_path, map_location=self._device))
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

