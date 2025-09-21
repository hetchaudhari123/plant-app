import httpx
from config.config import settings
from api_routes.endpoints import DELETE_PREDICTIONS_BY_USER, GET_MODEL_PREDICTION, CREATE_PREDICTION
async def delete_predictions_by_user(user_id: str):
    async with httpx.AsyncClient() as client:
        resp = await client.delete(
            settings.BACKEND_DB_URL + DELETE_PREDICTIONS_BY_USER.format(user_id=user_id)
        )
        resp.raise_for_status()
        return resp.json()
    

async def get_prediction(model_name: str, file):
    files = {"file": (file.filename, await file.read(), file.content_type)}
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            settings.BACKEND_MODEL_URL + GET_MODEL_PREDICTION.format(model_name = model_name)
            , files=files)
        resp.raise_for_status()
        return resp.json()
    

async def create_prediction(pred_doc: dict):
    """
    Calls db_service to insert a prediction document.

    Args:
        pred_doc (dict): The prediction document to insert

    Returns:
        dict: The inserted prediction document (with _id)
    """
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            settings.BACKEND_DB_URL + CREATE_PREDICTION,
            json=pred_doc
        )
        resp.raise_for_status()
        return resp.json()