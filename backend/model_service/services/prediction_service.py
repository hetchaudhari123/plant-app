from fastapi import UploadFile, HTTPException
from PIL import Image
import torch
from torchvision import transforms
from models.registry import manager

async def predict_model(model_name: str, file: UploadFile):
    try:
        # Open image
        image = Image.open(file.file).convert("RGB")

        # Transform image for PyTorch models
        transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor()
        ])
        input_tensor = transform(image).unsqueeze(0)  # Add batch dimension

        # Run prediction
        output = manager.predict(model_name, input_tensor)

        # Convert output to string (or JSON serializable)
        return {"model": model_name, "output": str(output)}

    except FileNotFoundError:
        raise HTTPException(status_code=400, detail="Invalid file")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")
