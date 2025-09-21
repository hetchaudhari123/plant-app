import db.connections as db_conn
from pydantic import EmailStr
from config.config import settings
from datetime import datetime, timezone, timedelta

async def delete_otps_by_email(email: EmailStr):
    result = await db_conn.otps_collection.delete_many({"email": email})
    return result.deleted_count

async def get_otp_by_code(otp_code: str):
    return await db_conn.otps_collection.find_one({"otp": otp_code})


async def create_otp(otp_doc: dict):

    result = await db_conn.otps_collection.insert_one(otp_doc)
    otp_doc["_id"] = str(result.inserted_id)  # serialize ObjectId
    return otp_doc


async def get_otp_by_email_and_code(email: str, otp: str):
    return await db_conn.otps_collection.find_one({"email": email, "otp": otp})


async def get_otp_by_email(email: str):
    otp_doc = await db_conn.otps_collection.find_one({"email": email})
    if otp_doc:
        otp_doc["_id"] = str(otp_doc["_id"])  # serialize ObjectId
    return otp_doc

async def delete_otps_by_user(user_id: str):
    result = await db_conn.otps_collection.delete_many({"user_id": user_id})
    return result.deleted_count


async def get_otp_for_email_change(user_id: str, email: EmailStr, otp: str, purpose: str):
    return await db_conn.otps_collection.find_one({
        "user_id": user_id,
        "email": email,
        "otp": otp,
        "purpose": purpose
    })