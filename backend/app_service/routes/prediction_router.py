from fastapi import APIRouter, UploadFile, Form, File, Depends
from fastapi import HTTPException
from services.prediction_service import predict_service
from dependencies.auth import require_user
router = APIRouter()


@router.post("/{model_name}")
async def create_prediction_endpoint(
    model_name: str,
    user=Depends(require_user),
    file: UploadFile = File(...)
):
    """
    Upload an image, call the model_service for prediction, 
    and save the result in db_service.
    """
    user_id=user.id  # get user_id from JWT
    if not file:
        raise HTTPException(status_code=400, detail="Image file is required")

    saved_doc = await predict_service(model_name, file, user_id)
    return saved_doc
