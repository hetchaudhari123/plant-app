import httpx
from config.config import settings
from api_routes.endpoints import DELETE_JOB_BY_USER_ID

async def delete_jobs_by_user(user_id: str):
    async with httpx.AsyncClient() as client:
        resp = await client.delete(settings.BACKEND_DB_URL + DELETE_JOB_BY_USER_ID.format(user_id=user_id))
        resp.raise_for_status()
        return resp.json()

