from fastapi import HTTPException, UploadFile
from datetime import datetime, timedelta
import time
from config.config import settings
import uuid
from datetime import datetime, timezone
from fastapi import UploadFile, HTTPException
import cloudinary
import cloudinary.uploader
from crud_apis.predictions_api import get_prediction, create_prediction
import db.connections as db_conn

async def predict_service(model_name: str, file: UploadFile, user_id: str):
    """
    Calls the model_service to get prediction and saves it in the predictions collection.
    
    Args:
        model_name (str): ID of the model to use
        file (UploadFile): Image uploaded by the user
        user_id (str): ID of the user making the request

    Returns:
        Prediction: saved prediction document
    """
    try:
        file.file.seek(0)
        upload_result = cloudinary.uploader.upload(
            file.file,
            folder="plant_app/plant_images",
            overwrite=True,
            resource_type="image"
        )
        plant_pic_url = upload_result["secure_url"]


        # --------------------------
        # Call model_service
        # --------------------------
        start_time = time.perf_counter()  # start timer
        file.file.seek(0)
        prediction_result = await get_prediction(model_name, file)  # returns dict with 'prediction', 'confidence', 'raw_output'
        end_time = time.perf_counter()  # end timer
        elapsed = end_time - start_time  # elapsed time in seconds
        # --------------------------
        # Prepare document to save
        # --------------------------
        prediction_id = str(uuid.uuid4())

        pred_doc = {
            "prediction_id": prediction_id,
            "model_name": model_name,
            "user_id": user_id,
            "image_url": plant_pic_url,  # replace with actual uploaded image URL if you store it in S3 or DB
            "status": "completed",  # or SUCCESS if immediately done
            "prediction": prediction_result.get("prediction"),
            "confidence": prediction_result.get("confidence"),
            "raw_output": prediction_result.get("raw_output"),
            "processing_time": elapsed,  # optional, fill if you measure time
        }

        # --------------------------
        # Save via db_service
        # --------------------------
        saved_doc = await db_conn.predictions_collection.insert_one(pred_doc)


        pred_doc["_id"] = str(saved_doc.inserted_id)
        return pred_doc

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")