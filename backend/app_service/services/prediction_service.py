from fastapi import HTTPException, UploadFile
from datetime import datetime, timedelta
import time
from config.config import settings
import uuid
from datetime import datetime, timezone
from fastapi import UploadFile, HTTPException
import cloudinary
import cloudinary.uploader
import db.connections as db_conn
import httpx
from api_routes.endpoints import GET_MODEL_PREDICTION
from models.prediction import PredictionStatus
from typing import List, Dict
from pathlib import Path
import json


async def get_prediction(model_name: str, file):
    files = {"file": (file.filename, await file.read(), file.content_type)}
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            settings.BACKEND_MODEL_URL + GET_MODEL_PREDICTION.format(model_name = model_name)
            , files=files)
        resp.raise_for_status()
        return resp.json()



async def predict_service(model_name: str, file: UploadFile, user_id: str, top_k: int = 5):
    """
    Calls the model_service to get prediction and saves it in the predictions collection.
    
    Args:
        model_name (str): ID of the model to use
        file (UploadFile): Image uploaded by the user
        user_id (str): ID of the user making the request
        top_k (int): Number of top predictions to return (default: 5)
    
    Returns:
        Prediction: saved prediction document with top k predictions
    """
    try:
        # Load idx2label mapping
        idx2label_path = Path("utils/idx2label.json")  # Update with actual path
        with open(idx2label_path, "r") as f:
            idx2label = json.load(f)
        
        # Upload image to Cloudinary
        file.file.seek(0)
        upload_result = cloudinary.uploader.upload(
            file.file,
            folder="plant_app/plant_images",
            overwrite=True,
            resource_type="image"
        )
        plant_pic_url = upload_result["secure_url"]

        # Call model_service
        start_time = time.perf_counter()
        file.file.seek(0)
        prediction_result = await get_prediction(model_name, file)
        end_time = time.perf_counter()
        elapsed = end_time - start_time

        # Parse predictions and get top k results
        top_predictions = parse_top_predictions(
            prediction_result, 
            idx2label, 
            top_k
        )
        
        # Extract primary (top 1) crop and disease from the main prediction
        primary_crop, primary_disease = parse_crop_disease(prediction_result.get("prediction", "unknown/unknown"))

        # Generate prediction ID
        prediction_id = str(uuid.uuid4())

        # Prepare document matching Prediction model
        pred_doc = {
            "prediction_id": prediction_id,
            "model_name": model_name,
            "user_id": user_id,
            "image_url": plant_pic_url,
            "status": PredictionStatus.completed,
            "crop": primary_crop,
            "disease": primary_disease,
            "raw_output": {
                "top_predictions": top_predictions,
                "primary_confidence": prediction_result.get("confidence"),
                "model": prediction_result.get("model"),
                "all_probabilities": prediction_result.get("raw_output")
            },
            "processing_time": elapsed,
            "created_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=settings.PREDICTION_EXPIRY_HOURS)
        }

        # Save to database
        saved_doc = await db_conn.predictions_collection.insert_one(pred_doc)

        # Add MongoDB _id to the document
        pred_doc["_id"] = str(saved_doc.inserted_id)
        
        return pred_doc

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


def parse_top_predictions(prediction_result: dict, idx2label: dict, top_k: int = 5) -> List[Dict]:
    """
    Parse prediction results and return top k predictions with crop and disease info.
    
    Args:
        prediction_result: Raw prediction result from model service
            Expected format: {
                "model": "mobilenet_v3_large",
                "prediction": "apple/apple scab",
                "confidence": 0.999808132648468,
                "raw_output": [0.999808132648468, 1.5604824511683546e-05, ...]
            }
        idx2label: Mapping from index to "crop/disease_name" format
        top_k: Number of top predictions to return
    
    Returns:
        List of dicts with crop, disease, confidence, and label info
    """
    predictions = []
    
    try:
        # Get raw probabilities array
        raw_output = prediction_result.get("raw_output", [])
        
        if not raw_output:
            return []
        
        # Create list of (index, probability) tuples
        indexed_probs = [(idx, prob) for idx, prob in enumerate(raw_output)]
        
        # Sort by probability (descending) and get top k
        sorted_predictions = sorted(indexed_probs, key=lambda x: x[1], reverse=True)[:top_k]
        
        for class_idx, confidence in sorted_predictions:
            # Get label from idx2label
            label = idx2label.get(str(class_idx), "unknown/unknown")
            
            # Parse crop and disease from label
            crop, disease = parse_crop_disease(label)
            
            predictions.append({
                "crop": crop,
                "disease": disease,
                "confidence": float(confidence),
                "label": label,
                "class_idx": class_idx
            })
    
    except Exception as e:
        print(f"Error parsing predictions: {e}")
        # Return a safe default with the primary prediction
        primary_label = prediction_result.get("prediction", "unknown/unknown")
        crop, disease = parse_crop_disease(primary_label)
        predictions = [{
            "crop": crop,
            "disease": disease,
            "confidence": prediction_result.get("confidence", 0.0),
            "label": primary_label,
            "class_idx": 0
        }]
    
    return predictions


def parse_crop_disease(label: str) -> tuple[str, str]:
    """
    Parse crop and disease from label string.
    Handles formats: "crop/disease", "crop / disease", "crop/ disease", "crop /disease"
    
    Args:
        label: String in format "crop/disease_name" (e.g., "apple/apple scab")
    
    Returns:
        Tuple of (crop, disease)
    """
    # Split by / and strip whitespace
    parts = [part.strip() for part in label.split('/')]
    
    if len(parts) >= 2:
        crop = parts[0]
        disease = parts[1]
    elif len(parts) == 1:
        # Only crop provided, no disease
        crop = parts[0]
        disease = "healthy"
    else:
        crop = "unknown"
        disease = "unknown"
    
    return crop, disease