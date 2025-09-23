import httpx
from config.config import settings
from api_routes.endpoints import GET_USER_BY_EMAIL, CREATE_USER, GET_USER_BY_ID, UPDATE_USER_PASSWORD, UPDATE_RESET_TOKEN, GET_USER_BY_RESET_TOKEN, UPDATE_USER_PROFILE, DELETE_USER, UPDATE_USER_PROFILE_PIC
from pydantic import EmailStr
from datetime import datetime, timezone
from typing import Optional

async def get_user_by_email(email: EmailStr):
    async with httpx.AsyncClient() as client:
        resp = await client.get(settings.BACKEND_DB_URL + GET_USER_BY_EMAIL.format(email=email))
        resp.raise_for_status()
        return resp.json()


async def create_user(user_doc: dict):
    async with httpx.AsyncClient() as client:
        resp = await client.post(settings.BACKEND_DB_URL + CREATE_USER, json=user_doc)
        resp.raise_for_status()
        return resp.json()
    

async def get_user_by_id(user_id: str):
    async with httpx.AsyncClient() as client:
        resp = await client.get(settings.BACKEND_DB_URL + GET_USER_BY_ID.format(user_id=user_id))
        resp.raise_for_status()
        return resp.json()

    

    
async def update_user_password(user_id: str, new_password_hash: str):
    async with httpx.AsyncClient() as client:
        resp = await client.put(
            settings.BACKEND_DB_URL + UPDATE_USER_PASSWORD.format(user_id=user_id),
            json={"new_password_hash": new_password_hash}
        )
        resp.raise_for_status()
        return resp.json()




async def update_reset_token(user_id: str, token: Optional[str], expires_at: Optional[datetime]):
    # Serialize to ISO format string
    expires_at_str = expires_at.isoformat() if expires_at else None
    async with httpx.AsyncClient() as client:
        resp = await client.put(
            settings.BACKEND_DB_URL + UPDATE_RESET_TOKEN.format(user_id=user_id),
            json={"token": token, "expires_at": expires_at_str}
        )
        resp.raise_for_status()
        return resp.json()
    


    
async def get_user_by_reset_token(token: str):
    async with httpx.AsyncClient() as client:
        resp = await client.get(settings.BACKEND_DB_URL + GET_USER_BY_RESET_TOKEN.format(token=token))
        resp.raise_for_status()
        return resp.json()
    


async def update_user_profile(user_id: str, update_fields: dict):
    async with httpx.AsyncClient() as client:
        resp = await client.put(
            settings.BACKEND_DB_URL + UPDATE_USER_PROFILE.format(user_id=user_id),
            json={"update_fields": update_fields}
        )
        resp.raise_for_status()
        return resp.json()



    

async def delete_user(user_id: str):
    async with httpx.AsyncClient() as client:
        resp = await client.delete(settings.BACKEND_DB_URL + DELETE_USER.format(user_id=user_id))
        resp.raise_for_status()
        return resp.json()



async def update_user_profile_pic(user_id: str, new_pic_url: str):
    async with httpx.AsyncClient() as client:
        resp = await client.put(
            settings.BACKEND_DB_URL + UPDATE_USER_PROFILE_PIC.format(user_id=user_id),
            json={"new_pic_url": new_pic_url}
        )
        resp.raise_for_status()
        return resp.json()