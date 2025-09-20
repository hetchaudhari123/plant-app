from fastapi import APIRouter
from crud.prediction_crud import delete_predictions_by_user  # import your CRUD function

router = APIRouter()

@router.delete("/user/{user_id}")
async def delete_predictions_by_user_endpoint(user_id: str):
    deleted_count = await delete_predictions_by_user(user_id)
    if deleted_count == 0:
        return {"deleted_count": 0, "message": "No predictions found for this user"}
    return {"deleted_count": deleted_count, "message": f"Deleted {deleted_count} predictions for user"}
