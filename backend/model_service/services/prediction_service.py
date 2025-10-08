from fastapi import UploadFile, HTTPException
from PIL import Image
from manager import ModelManager
from typing import List, Optional
from bson import ObjectId
import db.connections as db_conn


async def predict_service(
    model_name: str, file: UploadFile, manager: ModelManager, idx2label
):
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
                "raw_output": probs[0].tolist() if probs is not None else None,
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
                "raw_output": probs.tolist(),
            }

        return result

    except Exception as e:
        print("....THE ERROR....", str(e))
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


async def get_all_models_service(
    status: Optional[str] = None, model_type: Optional[str] = None
) -> List[dict]:
    """
    Fetch all model details from the database.

    Args:
        status: Optional filter by status (active/deprecated)
        model_type: Optional filter by model type (CNN, ResNet, etc.)

    Returns:
        List of model documents
    """
    try:
        # Build query filter
        query = {}
        if status:
            query["status"] = status
        if model_type:
            query["type"] = model_type

        # Fetch models from database
        cursor = db_conn.models_collection.find(query)
        models = await cursor.to_list(length=None)

        # Convert ObjectId to string for JSON serialization
        for model in models:
            if "_id" in model:
                model["_id"] = str(model["_id"])
            if "model_id" in model:
                model["model_id"] = str(model["model_id"])

        return models

    except Exception as e:
        print(f"Error fetching models: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch models: {str(e)}")


async def get_model_by_alias_service(alias: str) -> dict:
    """
    Fetch a specific model by its alias.

    Args:
        alias: Model alias (e.g., "densenet121")

    Returns:
        Model document
    """
    try:
        model = await db_conn.models_collection.find_one({"alias": alias})

        if not model:
            raise HTTPException(
                status_code=404, detail=f"Model with alias '{alias}' not found"
            )

        # Convert ObjectId to string
        if "_id" in model:
            model["_id"] = str(model["_id"])
        if "model_id" in model:
            model["model_id"] = str(model["model_id"])

        return model

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching model: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch model: {str(e)}")


async def get_active_models_service() -> List[dict]:
    """
    Fetch only active models.

    Returns:
        List of active model documents
    """
    return await get_all_models_service(status="active")


async def get_model_by_id_service(model_id: str) -> dict:
    """
    Fetch a specific model by its ID.

    Args:
        model_id: Model ID (ObjectId as string)

    Returns:
        Model document
    """
    try:
        # Validate ObjectId format
        if not ObjectId.is_valid(model_id):
            raise HTTPException(status_code=400, detail="Invalid model ID format")

        model = await db_conn.models_collection.find_one({"model_id": model_id})

        if not model:
            raise HTTPException(
                status_code=404, detail=f"Model with ID '{model_id}' not found"
            )

        # Convert ObjectId to string
        if "_id" in model:
            model["_id"] = str(model["_id"])
        if "model_id" in model:
            model["model_id"] = str(model["model_id"])

        return model

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching model: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch model: {str(e)}")
