from fastapi import APIRouter, UploadFile, Depends, File, Body
from manager.initializer import setup_models
from services.prediction_service import predict_service
from dependencies import get_manager, get_idx2label
from pydantic import BaseModel
from typing import Any, Optional
from services.prediction_service import get_all_models_service, get_active_models_service, get_model_by_alias_service, get_model_by_id_service
import db.connections as db_conn

router = APIRouter()

@router.post("/predict/{model_name}")
async def predict(
    model_name: str,
    file: UploadFile = File(...),
    manager = Depends(get_manager),
    idx2label = Depends(get_idx2label)
):
    """
    Upload an image and get prediction from the specified model.
    """
    # Call your service function, passing manager and IDX2LABEL
    result = await predict_service(model_name, file, manager,idx2label)
    return result


# Request body models
class ModelFilterRequest(BaseModel):
    status: Optional[str] = None
    model_type: Optional[str] = None

class ModelAliasRequest(BaseModel):
    alias: str

class ModelIdRequest(BaseModel):
    model_id: str


# GET endpoints (original)
@router.get("/models")
async def get_all_models(
    status: Optional[str] = None,
    model_type: Optional[str] = None
):
    """Get all models with optional filters via query parameters"""
    models = await get_all_models_service(status, model_type)
    return {"models": models, "count": len(models)}


@router.get("/models/active")
async def get_active_models():
    """Get only active models"""
    models = await get_active_models_service()
    return {"models": models, "count": len(models)}


@router.get("/models/alias/{alias}")
async def get_model_by_alias(alias: str):
    """Get model by alias via path parameter"""
    model = await get_model_by_alias_service(alias)
    return {"model": model}


@router.get("/models/{model_id}")
async def get_model_by_id(model_id: str):
    """Get model by ID via path parameter"""
    model = await get_model_by_id_service(model_id)
    return {"model": model}


# POST endpoints (for request body support in Postman)
@router.post("/models/search")
async def search_models(request: ModelFilterRequest = Body(...)):
    """Get all models with optional filters via request body"""
    models = await get_all_models_service(request.status, request.model_type)
    return {"models": models, "count": len(models)}


@router.post("/models/by-alias")
async def get_model_by_alias_post(request: ModelAliasRequest = Body(...)):
    """Get model by alias via request body"""
    model = await get_model_by_alias_service(request.alias)
    return {"model": model}


@router.post("/models/by-id")
async def get_model_by_id_post(request: ModelIdRequest = Body(...)):
    """Get model by ID via request body"""
    model = await get_model_by_id_service(request.model_id)
    return {"model": model}








@router.get("/debug/db-info")
async def debug_db_info():
    """Debug endpoint to check database connection"""
    collection_name = db_conn.models_collection.name if db_conn.models_collection is not None else "None"
    database_name = db_conn.db.name if db_conn.db is not None else "None"
    
    return {
        "collection_name": collection_name,
        "database_name": database_name,
        "collection_exists": db_conn.models_collection is not None
    }