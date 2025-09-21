from fastapi import UploadFile, HTTPException
from PIL import Image
from models import ModelManager

async def predict_service(model_name: str, file: UploadFile, manager: ModelManager, idx2label):
    try:
        # Load image
        image = Image.open(file.file).convert("RGB")

        # Predict
        output = manager.predict(model_name, image)

        # Handle sklearn vs torch output
        if model_name == "ensemble":
            prediction, probs = output  # unpack tuple
            predicted_idx = int(prediction[0])
            predicted_class = idx2label[str(predicted_idx)]
            confidence = float(probs[0][predicted_idx]) if probs is not None else None

            result = {
                "model": model_name,
                "prediction": predicted_class,
                "confidence": confidence,
                "raw_output": probs[0].tolist() if probs is not None else None
            }

        else:
            probs = output[0]  # since output is (1, num_classes) numpy array
            predicted_idx = int(probs.argmax())
            predicted_class = idx2label[str(predicted_idx)]
            confidence = float(probs[predicted_idx])

            result = {
                "model": model_name,
                "prediction": predicted_class,
                "confidence": confidence,
                "raw_output": probs.tolist()
            }


        return result

    except Exception as e:
        print("....THE ERROR....", str(e))
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")