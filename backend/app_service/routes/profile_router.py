# app/routes/profile_router.py
from fastapi import APIRouter, UploadFile, File, Response, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from services.profile_service import (
    update_profile_name,
    delete_account,
    update_profile_picture,
    request_email_change,
    confirm_email_change
)

router = APIRouter()

# --------------------
# Request Schemas
# --------------------
class UpdateNameSchema(BaseModel):
    user_id: str
    first_name: str | None = None
    last_name: str | None = None

class DeleteAccountSchema(BaseModel):
    user_id: str

class EmailChangeRequestSchema(BaseModel):
    user_id: str
    new_email: EmailStr
    current_password: str

class ConfirmEmailChangeSchema(BaseModel):
    user_id: str
    new_email: EmailStr
    otp_code: str

# --------------------
# Routes
# --------------------
@router.put("/update-name", summary="Update first and/or last name")
async def route_update_name(payload: UpdateNameSchema):
    await update_profile_name(
        user_id=payload.user_id,
        first_name=payload.first_name,
        last_name=payload.last_name
    )
    return {"message": "Profile name updated successfully"}


@router.delete("/delete-account", summary="Delete user account")
async def route_delete_account(payload: DeleteAccountSchema, response: Response):
    await delete_account(user_id=payload.user_id, response=response)
    return {"message": "Account deleted successfully"}


@router.put("/update-profile-picture", summary="Update profile picture")
async def route_update_profile_picture(user_id: str, file: UploadFile = File(...)):
    await update_profile_picture(user_id=user_id, file=file)
    return {"message": "Profile picture updated successfully"}


@router.post("/request-email-change", summary="Request to change email")
async def route_request_email_change(payload: EmailChangeRequestSchema):
    await request_email_change(
        user_id=payload.user_id,
        new_email=payload.new_email,
        current_password=payload.current_password
    )
    return {"message": "Email change OTP sent successfully"}


@router.post("/confirm-email-change", summary="Confirm email change with OTP")
async def route_confirm_email_change(payload: ConfirmEmailChangeSchema):
    await confirm_email_change(
        user_id=payload.user_id,
        new_email=payload.new_email,
        otp_code=payload.otp_code
    )
    return {"message": "Email changed successfully"}
