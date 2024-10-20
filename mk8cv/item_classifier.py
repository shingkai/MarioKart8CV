import torch
import torch.nn as nn
from torchvision import models, transforms
import cv2
from cv2.typing import MatLike

from state import Player, Stat, PlayerState, Item
from aois import CROP_COORDS

# ordered list of item classes that the model was trained on
class_names = [
    Item.BANANA,
    Item.TRIPLE_BANANA,
    Item.GREEN_SHELL,
    Item.TRIPLE_GREEN_SHELL,
    Item.RED_SHELL,
    Item.BLUE_SHELL,
    Item.MUSHROOM,
    Item.TRIPLE_MUSHROOM,
    Item.GOLDEN_MUSHROOM,
    Item.BULLET_BILL,
    Item.BLOOPER,
    Item.STAR,
    Item.FIRE_FLOWER,
    Item.PIRANHA_PLANT,
    Item.SUPER_HORN,
    Item.COIN,
    Item.BOO,
    Item.NONE,
]

classes = ['01', '02', '03', '04', '05', '07', '09', '10', '11', '12', '13', '15', '16', '18', '19', '21', '23', '24']


# # Check if GPU is available (either cuda for nvidia or mps for apple silicon)
device = torch.device("cuda:0" if torch.cuda.is_available() else torch.device("mps") if torch.backends.mps.is_available() else  torch.device("cpu"))


def load_model(model_path):
    model = models.mobilenet_v3_large(pretrained=False)
    # Modify the classifier to match your number of classes
    num_classes = len(classes)  # Replace with the number of classes in your dataset
    model.classifier[3] = nn.Linear(model.classifier[3].in_features, num_classes)

    # Load the saved state dict
    model.load_state_dict(torch.load(model_path, map_location=device))
    model = model.to(device)
    model.eval()
    return model


model = load_model('./models/image_classifier_mobilenetv3.pth')


img_width, img_height = 96, 96
preprocess = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((img_width, img_height)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])


# Function to predict on a cv2 frame
def predict_frame(frame, preprocess=preprocess):
    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image = preprocess(image).unsqueeze(0).to(device)

    with torch.no_grad():
        output = model(image)
        _, predicted = torch.max(output, 1)

    predicted_class = classes[predicted.item()]
    return predicted_class


def extract_player_items(frame: MatLike, player: Player) -> tuple[Item, Item]:
    """Extracts the player's items from the frame."""
    height, width, channels = frame.shape

    item1_coords = CROP_COORDS[player][Stat.ITEM1]
    item1 = predict_frame(frame[round(height * item1_coords[2]): round(height * item1_coords[3]), round(width * item1_coords[0]): round(width * item1_coords[1])])

    item2_coords = CROP_COORDS[player][Stat.ITEM2]
    item2 = predict_frame(frame[round(height * item2_coords[2]): round(height * item2_coords[3]), round(width * item2_coords[0]): round(width * item2_coords[1])])

    return Item(int(item1)), Item(int(item2))
