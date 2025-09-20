import httpx
from config.config import settings
from pydantic import EmailStr
from api_routes.endpoints import DELETE_OTPS_BY_EMAIL, GET_OTP_BY_CODE, CREATE_OTP, GET_OTP_BY_EMAIL_AND_CODE, GET_OTP_BY_EMAIL, DELETE_OTPS_BY_USER, GET_OTP_FOR_EMAIL_CHANGE


async def delete_otps_for_email(email: EmailStr):
    async with httpx.AsyncClient() as client:
        resp = await client.delete(settings.BACKEND_DB_URL + DELETE_OTPS_BY_EMAIL.format(email=email))
        resp.raise_for_status()
        return resp.json()

async def get_otp_by_code(otp_code: str):
    async with httpx.AsyncClient() as client:
        resp = await client.get(settings.BACKEND_DB_URL + GET_OTP_BY_CODE.format(otp_code=otp_code))
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()
    

async def create_otp(otp_doc: dict):
    async with httpx.AsyncClient() as client:
        resp = await client.post(settings.BACKEND_DB_URL + CREATE_OTP, json=otp_doc)
        resp.raise_for_status()
        return resp.json()
    
    
async def get_otp_by_email_and_code(email: str, otp: str):
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            settings.BACKEND_DB_URL + GET_OTP_BY_EMAIL_AND_CODE,
            params={"email": email, "otp": otp}
        )
        resp.raise_for_status()
        return resp.json()
    
async def get_otp_by_email(email: EmailStr):
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            settings.BACKEND_DB_URL + GET_OTP_BY_EMAIL,
            params={"email": email}
        )
        resp.raise_for_status()
        return resp.json()

async def delete_otps_by_user(user_id: str):
    async with httpx.AsyncClient() as client:
        resp = await client.delete(
            settings.BACKEND_DB_URL + DELETE_OTPS_BY_USER.format(user_id=user_id)
        )
        resp.raise_for_status()
        return resp.json()

async def get_otp_for_email_change(user_id: str, email: EmailStr, otp: str):
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            settings.BACKEND_DB_URL + GET_OTP_FOR_EMAIL_CHANGE,
            params={
                "user_id": user_id,
                "email": email,
                "otp": otp,
                "purpose": "email_change"
            }
        )
        resp.raise_for_status()
        return resp.json()