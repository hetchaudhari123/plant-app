# dependencies.py
from manager.initializer import setup_models

# Initialize once at import
manager, IDX2LABEL = setup_models(idx2label_path="saved_models/utils/idx2label.json")

def get_manager():
    return manager

def get_idx2label():
    return IDX2LABEL
