import json
import torch
from models.plant_model import PlantModel
from models.manager import ModelManager
from config.config import settings
from saved_models.model_paths.model_paths import RESNET50_PATH, DENSENET121_PATH, EFFICIENTNET_B4_PATH, ENSEMBLE_PATH, MOBILENET_V3_PATH



# initializer.py
def setup_models(idx2label_path="saved_models/utils/idx2label.json"):

    with open(idx2label_path, "r") as f:
        IDX2LABEL = json.load(f)

    manager = ModelManager()



    # Register base PyTorch models
    manager.register_model(PlantModel(
        name="resnet50",
        model_path=RESNET50_PATH,
        model_type="pytorch",
        num_classes=settings.NUM_CLASSES  # set your number of classes here
    ))
    manager.register_model(PlantModel(
        name="efficientnet_b4",
        model_path=EFFICIENTNET_B4_PATH,
        model_type="pytorch",
        num_classes=settings.NUM_CLASSES
    ))
    manager.register_model(PlantModel(
        name="mobilenet_v3_large",
        model_path=MOBILENET_V3_PATH,
        model_type="pytorch",
        num_classes=settings.NUM_CLASSES
    ))
    manager.register_model(PlantModel(
        name="densenet121",
        model_path=DENSENET121_PATH,
        model_type="pytorch",
        num_classes=settings.NUM_CLASSES
    ))

    # Register ensemble model with a defined stacking order
    manager.register_model(PlantModel(
        name="ensemble",
        model_path=ENSEMBLE_PATH,
        model_type="sklearn",
        model_order=['densenet121', 'efficientnet_b4', 'mobilenet_v3_large', 'resnet50']  # must match training order
    ))
    
    return manager, IDX2LABEL


