# model_paths.py

# Base directory where the models are saved
BASE_MODEL_DIR = "saved_models"

# Individual PyTorch models
RESNET50_PATH = f"{BASE_MODEL_DIR}/resnet50_final_finetuned.pth"
DENSENET121_PATH = f"{BASE_MODEL_DIR}/densenet121_final_finetuned.pth"
MOBILENET_V3_PATH = f"{BASE_MODEL_DIR}/mobilenet_v3_large_final_finetuned.pth"
EFFICIENTNET_B4_PATH = f"{BASE_MODEL_DIR}/efficientnet_b4_final_finetuned.pth"

# Ensemble model (sklearn)
ENSEMBLE_PATH = f"{BASE_MODEL_DIR}/logistic_meta_model.pkl"
