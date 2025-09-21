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


async def predict_service(model_id: str, file: UploadFile, user_id: str):
    """
    Calls the model_service to get prediction and saves it in the predictions collection.
    
    Args:
        model_id (str): ID of the model to use
        file (UploadFile): Image uploaded by the user
        user_id (str): ID of the user making the request

    Returns:
        Prediction: saved prediction document
    """
    try:
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
        prediction_result = await get_prediction(model_id, file)  # returns dict with 'prediction', 'confidence', 'raw_output'
        end_time = time.perf_counter()  # end timer
        elapsed = end_time - start_time  # elapsed time in seconds
        # --------------------------
        # Prepare document to save
        # --------------------------
        prediction_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        pred_doc = {
            "prediction_id": prediction_id,
            "model_id": model_id,
            "user_id": user_id,
            "image_url": plant_pic_url,  # replace with actual uploaded image URL if you store it in S3 or DB
            "status": "completed",  # or SUCCESS if immediately done
            "prediction": prediction_result.get("prediction"),
            "confidence": prediction_result.get("confidence"),
            "raw_output": prediction_result.get("raw_output"),
            "processing_time": elapsed,  # optional, fill if you measure time
            "created_at": now,
            "expires_at": now + timedelta(hours=settings.PREDICTION_EXPIRY_HOURS)  # optional expiration
        }

        # --------------------------
        # Save via db_service
        # --------------------------
        saved_doc = await create_prediction(pred_doc)

        return saved_doc

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")