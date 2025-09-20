from fastapi import APIRouter, HTTPException
from pydantic import EmailStr

from crud.otp_crud import (
    delete_otps_by_email,
    get_otp_by_code,
    create_otp,
    get_otp_by_email_and_code,
    get_otp_by_email,
    delete_otps_by_user,
    get_otp_for_email_change
)

router = APIRouter()

# DELETE OTPs by email
@router.delete("/{email}")
async def delete_otps_by_email_endpoint(email: EmailStr):
    deleted_count = await delete_otps_by_email(email)
    return {"deleted_count": deleted_count, "message": f"Deleted {deleted_count} OTPs for {email}"}

# GET OTP by code
@router.get("/code/{otp_code}")
async def get_otp_by_code_endpoint(otp_code: str):
    otp_doc = await get_otp_by_code(otp_code)
    if not otp_doc:
        raise HTTPException(status_code=404, detail="OTP not found")
    otp_doc["_id"] = str(otp_doc["_id"])
    return otp_doc

# CREATE OTP
@router.post("/")
async def create_otp_endpoint(otp_doc: dict):
    created_otp = await create_otp(otp_doc)
    return created_otp

# GET OTP by email and code
@router.get("/verify")
async def get_otp_by_email_and_code_endpoint(email: str, otp: str):
    otp_doc = await get_otp_by_email_and_code(email, otp)
    if not otp_doc:
        raise HTTPException(status_code=404, detail="OTP not found")
    otp_doc["_id"] = str(otp_doc["_id"])
    return otp_doc

# GET OTP by email (first matching)
@router.get("/email")
async def get_otp_by_email_endpoint(email: EmailStr):
    otp_doc = await get_otp_by_email(email)
    if not otp_doc:
        raise HTTPException(status_code=404, detail="OTP not found")
    return otp_doc

# DELETE OTPs by user_id
@router.delete("/user/{user_id}")
async def delete_otps_by_user_endpoint(user_id: str):
    deleted_count = await delete_otps_by_user(user_id)
    return {"deleted_count": deleted_count, "message": f"Deleted {deleted_count} OTPs for user {user_id}"}

# GET OTP for email change (with purpose)
@router.get("/email-change")
async def get_otp_for_email_change_endpoint(user_id: str, email: EmailStr, otp: str, purpose: str):
    otp_doc = await get_otp_for_email_change(user_id, email, otp, purpose)
    if not otp_doc:
        raise HTTPException(status_code=404, detail="OTP not found")
    otp_doc["_id"] = str(otp_doc["_id"])
    return otp_doc
