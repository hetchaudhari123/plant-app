import httpx
from config.config import settings
from api_routes.endpoints import DELETE_PREDICTIONS_BY_USER
async def delete_predictions_by_user(user_id: str):
    async with httpx.AsyncClient() as client:
        resp = await client.delete(
            settings.BACKEND_DB_URL + DELETE_PREDICTIONS_BY_USER.format(user_id=user_id)
        )
        resp.raise_for_status()
        return resp.json()