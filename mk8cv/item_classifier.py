import torch
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

# # Check if GPU is available (either cuda for nvidia or mps for apple silicon)
device = torch.device("cuda:0" if torch.cuda.is_available() else torch.device("mps") if torch.backends.mps.is_available() else  torch.device("cpu"))

def load_model(model_path: str):
    # Load the model architecture
    model = models.vgg16(pretrained=False)
     # Adjust final layer to match output classes
    model.fc = torch.nn.Linear(model.fc.in_features, len(class_names)) 
    # Load the saved weights
    model.load_state_dict(torch.load(model_path, map_location=device))
    # Set the model to evaluation mode
    model.eval()
    # Move the model to the appropriate device (MPS or CPU)
    model = model.to(device)

    return model

model = load_model('models/item_classifier_vgg16.pth')
# model = load_model('/home/itsgrimetime/code/MarioKart8CV/notebooks/best_model_vgg16.pth')


# Define the transformation to be applied to the input image (same as used during training)
preprocess = transforms.Compose([
    transforms.ToPILImage(),  # Convert numpy array (cv2) to PIL image
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

def predict_image(frame) -> str:
    # Preprocess the image
    img = preprocess(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    
    # Add batch dimension (PyTorch models expect a batch of images)
    img = img.unsqueeze(0)
    
    # Move the image to the same device as the model (MPS or CPU)
    img = img.to(device)
    
    # Turn off gradients for inference (faster and reduces memory usage)
    with torch.no_grad():
        outputs = model(img)
    
    # Get the predicted class (with the highest score)
    _, predicted_class = torch.max(outputs, 1)
    
    # Map the predicted class index to the class name
    predicted_class_name = class_names[predicted_class.item()]
    
    return predicted_class_name

def extract_player_items(frame: MatLike, player: Player, state: PlayerState) -> PlayerState:
    """Extracts the player's items from the frame."""
    height, width, channels = frame.shape

    item1_coords = CROP_COORDS[player][Stat.ITEM1]
    item1 = predict_image(frame[round(height * item1_coords[2]): round(height * item1_coords[3]), round(width * item1_coords[0]): round(width * item1_coords[1])])

    item2_coords = CROP_COORDS[player][Stat.ITEM2]
    item2 = predict_image(frame[round(height * item2_coords[2]): round(height * item2_coords[3]), round(width * item2_coords[0]): round(width * item2_coords[1])])

    state.item1 = Item(int(item1))
    state.item2 = Item(int(item2))
    return state
