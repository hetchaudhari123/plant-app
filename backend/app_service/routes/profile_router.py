from fastapi import APIRouter, UploadFile, File, Response, Depends, HTTPException, Depends, Body
from pydantic import BaseModel, EmailStr, Field
from services.profile_service import (
    update_profile_name,
    delete_account,
    update_profile_picture,
    request_email_change,
    confirm_email_change,
    get_user_details,
    get_user_by_id,
    get_primary_crops_for_user
)
from dependencies.auth import require_user
from dependencies.auth import require_user, AuthUser
from schemas.UserDashboardResponseSchema import UserDashboardResponse  
from services.profile_service import get_user_dashboard, update_farm_size
from typing import List
from models.user import User

router = APIRouter()

# --------------------
# Request Schemas
# --------------------
class UpdateNameSchema(BaseModel):
    first_name: str | None = None
    last_name: str | None = None

class DeleteAccountSchema(BaseModel):
    user_id: str

class EmailChangeRequestSchema(BaseModel):
    new_email: EmailStr
    current_password: str

class ConfirmEmailChangeSchema(BaseModel):
    new_email: EmailStr
    otp_code: str
    old_email: EmailStr

# --------------------
# Routes
# --------------------
@router.put("/update-name", summary="Update first and/or last name")
async def route_update_name(
    payload: UpdateNameSchema,
    user=Depends(require_user)  # inject authenticated user here
):
    user_id=user.id  # get user_id from JWT
    await update_profile_name(
        user_id=user_id,
        first_name=payload.first_name,
        last_name=payload.last_name
    )
    return {"message": "Profile name updated successfully"}


# Pydantic schema for request validation
class DeleteAccountSchema(BaseModel):
    password: str = Field(..., min_length=1, description="User's password for verification")

@router.delete("/delete-account", summary="Delete user account")
async def route_delete_account(
    payload: DeleteAccountSchema,
    response: Response,
    user=Depends(require_user)  # inject authenticated user
):
    user_id = user.id
    await delete_account(user_id=user_id, password=payload.password, response=response)
    return {"message": "Account deleted successfully"}



@router.put("/update-profile-picture", summary="Update profile picture")
async def route_update_profile_picture(
    user=Depends(require_user),  # inject authenticated user
    file: UploadFile = File(...)):
    user_id=user.id
    resp = await update_profile_picture(user_id=user_id, file=file)
    return resp   # already a dict, FastAPI will convert to JSON


@router.post("/request-email-change", summary="Request to change email")
async def route_request_email_change(
    payload: EmailChangeRequestSchema,
    user=Depends(require_user)  # inject authenticated user
):
    user_id=user.id  # get user_id from JWT

    await request_email_change(
        user_id=user_id,              # use backend-provided ID
        new_email=payload.new_email,
        current_password=payload.current_password
    )
    return {"message": "Email change OTP sent successfully"}


@router.post("/confirm-email-change", summary="Confirm email change with OTP")
async def route_confirm_email_change(
    payload: ConfirmEmailChangeSchema,
    user=Depends(require_user)  # inject authenticated user
):
    user_id=user.id  # get user_id from JWT

    await confirm_email_change(
        user_id=user_id,              # use backend-provided ID
        new_email=payload.new_email,
        old_email=payload.old_email,
        otp_code=payload.otp_code
    )
    return {"message": "Email changed successfully"}



@router.get("/users", summary="Get user by ID")
async def route_get_user_details(user: AuthUser  = Depends(require_user)):
    """
    Get user info by ID. Excludes sensitive fields like password and reset tokens.
    """
    user = await get_user_details(user.id)
    return {"success": True, "data": user, "message": "User fetched successfully"}


@router.get("/user/{user_id}", summary="Get user by ID")
async def route_get_user_by_id(user_id: str):
    """
    Get user info by ID. Excludes sensitive fields like password and reset tokens.
    """
    user = await get_user_by_id(user_id)
    return {
        "success": True,
        "data": user,
        "message": "User fetched successfully"
    }




@router.get("/users/get-dashboard-details", response_model=UserDashboardResponse)
async def dashboard(user = Depends(require_user)):
    """
    Returns aggregated dashboard metrics for the logged-in user.
    """

    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        dashboard_data = await get_user_dashboard(user_id=user.id)
        return dashboard_data
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    




@router.get("/users/primary-crops", response_model=List[str])
async def primary_crops(current_user: User = Depends(require_user), top_n: int = 3):
    """
    Returns the top N primary crops for the logged-in user.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    primary = await get_primary_crops_for_user(user_id=current_user.id, top_n=top_n)
    return primary

class UpdateFarmSizeSchema(BaseModel):
    farm_size: str


@router.put("/users/update-farm-size")
async def route_update_farm_size(
    payload: UpdateFarmSizeSchema,
    current_user = Depends(require_user)
):
    updated_user = await update_farm_size(current_user.id, payload.farm_size)
    if "_id" in updated_user:
        updated_user["_id"] = str(updated_user["_id"])
    return {"message": "Farm size updated successfully", "user": updated_user}
