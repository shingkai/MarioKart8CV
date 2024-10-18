import torch
import torch.nn as nn
from torchvision import models, transforms
import cv2
from cv2.typing import MatLike

from state import Player, Stat, PlayerState, Item
from aois import CROP_COORDS



# # Check if GPU is available (either cuda for nvidia or mps for apple silicon)
device = torch.device("cuda:0" if torch.cuda.is_available() else torch.device("mps") if torch.backends.mps.is_available() else  torch.device("cpu"))


def load_model(model_path):
    # Load the fine-tuned MobileNetV3 model
    model = models.mobilenet_v3_large(pretrained=False)
    num_classes = 13
    model.classifier[3] = nn.Linear(model.classifier[3].in_features, num_classes)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model = model.to(device)
    model.eval()
    return model


model = load_model('./models/position_classifier_mobilenetv3.pth')


# Transform for inference (96x96 resizing and normalization)
img_width, img_height = 96, 96
transform = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((img_width, img_height)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])


def predict_frame(frame: MatLike):
    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image = transform(image).unsqueeze(0).to(device)

    # Run the model in evaluation mode
    with torch.no_grad():
        outputs = model(image)
        _, predicted = torch.max(outputs, 1)

    return predicted.item()


def extract_player_position(frame: MatLike, player: Player, state: PlayerState) -> PlayerState:
    height, width, channels = frame.shape

    position_coords = CROP_COORDS[player][Stat.POSITION]
    position = predict_frame(frame=frame[round(height * position_coords[2]): round(height * position_coords[3]), round(width * position_coords[0]): round(width * position_coords[1])])

    state.position = position
    return state
