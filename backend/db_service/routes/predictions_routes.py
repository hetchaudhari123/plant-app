from fastapi import APIRouter, Body
from crud.prediction_crud import delete_predictions_by_user, insert_prediction  # import your CRUD function

router = APIRouter()

@router.delete("/user/{user_id}")
async def delete_predictions_by_user_endpoint(user_id: str):
    deleted_count = await delete_predictions_by_user(user_id)
    if deleted_count == 0:
        return {"deleted_count": 0, "message": "No predictions found for this user"}
    return {"deleted_count": deleted_count, "message": f"Deleted {deleted_count} predictions for user"}

@router.post("/create-prediction")
async def create_prediction_endpoint(pred_doc: dict = Body(...)):
    """
    Insert a prediction document into the database.
    """
    saved_doc = await insert_prediction(pred_doc)
    return {"message": "Prediction inserted successfully", "prediction": saved_doc}