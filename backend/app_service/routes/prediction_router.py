from fastapi import APIRouter, UploadFile, Form
from fastapi import HTTPException
from services.prediction_service import predict_service

router = APIRouter()


@router.post("/{model_id}")
async def create_prediction_endpoint(
    model_id: str,
    user_id: str = Form(...),   # send user_id as form field
    file: UploadFile = None
):
    """
    Upload an image, call the model_service for prediction, 
    and save the result in db_service.
    """
    if not file:
        raise HTTPException(status_code=400, detail="Image file is required")

    saved_doc = await predict_service(model_id, file, user_id)
    return saved_doc
