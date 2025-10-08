from fastapi import APIRouter, UploadFile, File, Depends
from fastapi import HTTPException
from services.prediction_service import (
    predict_service,
    get_user_predictions,
    delete_prediction,
)
from dependencies.auth import require_user
from pydantic import BaseModel, Field

router = APIRouter()


class PaginationRequest(BaseModel):
    skip: int = Field(default=0, ge=0, description="Number of records to skip")
    limit: int = Field(
        default=5, ge=1, le=1000, description="Maximum number of records to return"
    )
    sort_by: str = Field(default="created_at", description="Field to sort by")
    sort_order: int = Field(
        default=-1,
        ge=-1,
        le=1,
        description="Sort order: -1 for descending, 1 for ascending",
    )


@router.post("/get-user-predictions")
async def get_user_predictions_endpoint(
    pagination: PaginationRequest = PaginationRequest(), user=Depends(require_user)
):
    """
    Get all predictions for the authenticated user with pagination and sorting.
    """
    user_id = user.id  # get user_id from JWT
    result = await get_user_predictions(
        user_id=user_id,
        skip=pagination.skip,
        limit=pagination.limit,
        sort_by=pagination.sort_by,
        sort_order=pagination.sort_order,
    )

    return result


class DeletePredictionRequest(BaseModel):
    prediction_id: str


@router.post("/delete-prediction")
async def delete_prediction_endpoint(
    request: DeletePredictionRequest, user=Depends(require_user)
):
    """
    Delete a specific prediction for the authenticated user.

    Args:
        request: JSON body containing prediction_id
        user: Authenticated user from JWT token

    Returns:
        Success message with deleted prediction_id

    Raises:
        HTTPException 404: If prediction not found or doesn't belong to user
        HTTPException 500: If server error occurs
    """
    try:
        user_id = user.id  # get user_id from JWT
        result = await delete_prediction(
            prediction_id=request.prediction_id, user_id=user_id
        )
        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to delete prediction")


@router.post("/{model_name}")
async def create_prediction_endpoint(
    model_name: str, user=Depends(require_user), file: UploadFile = File(...)
):
    """
    Upload an image, call the model_service for prediction,
    and save the result in db_service.
    """
    user_id = user.id  # get user_id from JWT
    if not file:
        raise HTTPException(status_code=400, detail="Image file is required")

    saved_doc = await predict_service(model_name, file, user_id)
    return saved_doc
