from models.plant_model import PlantModel
from models.manager import ModelManager

manager = ModelManager()

# Register base PyTorch models
manager.register_model(PlantModel(
    name="resnet50",
    model_path="saved_models/resnet50_final_finetuned.pth",
    model_type="pytorch",
    num_classes=NUM_CLASSES  # set your number of classes here
))
manager.register_model(PlantModel(
    name="efficientnet_b4",
    model_path="saved_models/efficientnet_b4_final_finetuned.pth",
    model_type="pytorch",
    num_classes=NUM_CLASSES
))
manager.register_model(PlantModel(
    name="mobilenet_v3_large",
    model_path="saved_models/mobilenet_v3_large_final_finetuned.pth",
    model_type="pytorch",
    num_classes=NUM_CLASSES
))
manager.register_model(PlantModel(
    name="densenet121",
    model_path="saved_models/densenet121_final_finetuned.pth",
    model_type="pytorch",
    num_classes=NUM_CLASSES
))

# Register ensemble model with a defined stacking order
manager.register_model(PlantModel(
    name="ensemble",
    model_path="saved_models/logistic_meta_model.pkl",
    model_type="sklearn",
    model_order=['densenet121', 'efficientnet_b4', 'mobilenet_v3_large', 'resnet50']  # must match training order
))
