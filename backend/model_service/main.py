from fastapi import FastAPI, UploadFile
from PIL import Image
import models.registry

app = FastAPI()




# Prediction endpoint
@app.post("/predict/{model_name}")
async def predict(model_name: str, file: UploadFile):
    image = Image.open(file.file).convert("RGB")
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor()
    ])
    input_tensor = transform(image).unsqueeze(0)  # add batch dim
    output = manager.predict(model_name, input_tensor)
    return {"model": model_name, "output": str(output)}
