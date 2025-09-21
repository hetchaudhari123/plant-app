import httpx
from config.config import settings
from api_routes.endpoints import DELETE_PREDICTIONS_BY_USER, MODEL_SERVICE_URL
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
            settings.BACKEND_MODEL_URL + MODEL_SERVICE_URL.format(model_name = model_name)
            , files=files)
        resp.raise_for_status()
        return resp.json()