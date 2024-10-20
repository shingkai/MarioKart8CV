from abc import ABC, abstractmethod
import torch
import torch.nn as nn
from torchvision import models, transforms
import cv2
from cv2.typing import MatLike

from state import Player, Stat, Item
from aois import CROP_COORDS

# 
classes = ['01', '02', '03', '04', '05', '07', '09', '10', '11', '12', '13', '15', '16', '18', '19', '21', '23', '24']


class ItemClassifier(ABC):
    def __init__(self):
        self._model = None
        # Use GPU if available (cuda or apple silicon)
        self._device = torch.device("cuda:0" if torch.cuda.is_available() else torch.device("mps") if torch.backends.mps.is_available() else  torch.device("cpu"))
        self._classes = classes

    @abstractmethod
    def load(self, model_path: str) -> None:
        pass

    @abstractmethod
    def _predict(self, frame: MatLike) -> str:
        pass

    def extract_player_items(self, frame: MatLike, player: Player) -> tuple[Item, Item]:
        """Extracts the player's items from the frame."""
        height, width, channels = frame.shape

        item1_coords = CROP_COORDS[player][Stat.ITEM1]
        item1 = self._predict(frame[round(height * item1_coords[2]): round(height * item1_coords[3]), round(width * item1_coords[0]): round(width * item1_coords[1])])

        item2_coords = CROP_COORDS[player][Stat.ITEM2]
        item2 = self._predict(frame[round(height * item2_coords[2]): round(height * item2_coords[3]), round(width * item2_coords[0]): round(width * item2_coords[1])])

        return Item(int(item1)), Item(int(item2))


class MobileNetV3ItemClassifier(ItemClassifier):
    def __init__(self):
        super().__init__()

    def load(self, model_path='./models/image_classifier_mobilenetv3.pth'):
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


class ResNet18ItemClassifier(ItemClassifier):
    def __init__(self):
        super().__init__()

    def load(self, model_path='./models/item_classifier_resnet18.pth'):
        self._model = models.resnet18(pretrained=False)
        num_classes = len(self._classes)
        self._model.fc = torch.nn.Linear(self._model.fc.in_features, num_classes)
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
