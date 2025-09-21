from fastapi import APIRouter, UploadFile, Depends
from models.initializer import setup_models
from services.prediction_service import predict_service
from dependencies import get_manager, get_idx2label

router = APIRouter()

@router.post("/predict/{model_name}")
async def predict(
    model_name: str,
    file: UploadFile,
    manager = Depends(get_manager),
    idx2label = Depends(get_idx2label)
):
    """
    Upload an image and get prediction from the specified model.
    """
    # Call your service function, passing manager and IDX2LABEL
    result = await predict_service(model_name, file, manager,idx2label)
    return result
