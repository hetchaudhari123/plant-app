from fastapi import APIRouter, HTTPException
from pydantic import EmailStr, BaseModel
import datetime
from crud.user_crud import get_user_by_email, create_user, get_user_by_id, update_user_password, update_reset_token, get_user_by_reset_token, update_user_profile,delete_user, update_user_profile_pic

router = APIRouter()

# Request models for PUT endpoints
class UpdatePasswordRequest(BaseModel):
    new_password_hash: str

class UpdateResetTokenRequest(BaseModel):
    token: str
    expires_at: str

class UpdateProfileRequest(BaseModel):
    update_fields: dict

class UpdateProfilePicRequest(BaseModel):
    new_pic_url: str



@router.get("/email/{email}")
async def get_user_by_email_endpoint(email: EmailStr):
    user_doc = await get_user_by_email(email)
    if user_doc:
        user_doc["_id"] = str(user_doc["_id"])
    return user_doc  # returns None if not found

# CREATE a new user
@router.post("/")
async def create_user_endpoint(user_doc: dict):
    created_user = await create_user(user_doc)
    return created_user

# GET user by ID
@router.get("/{user_id}")
async def get_user_by_id_endpoint(user_id: str):
    user_doc = await get_user_by_id(user_id)
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    user_doc["_id"] = str(user_doc["_id"])
    return user_doc






# UPDATE user password
@router.put("/{user_id}/password")
async def update_user_password_endpoint(user_id: str, payload: UpdatePasswordRequest):
    updated_user = await update_user_password(user_id, payload.new_password_hash)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user

# UPDATE reset token
@router.put("/{user_id}/reset-token")
async def update_reset_token_endpoint(user_id: str, payload: UpdateResetTokenRequest):
    expires_at_dt = (payload.expires_at)

    result = await update_reset_token(user_id, payload.token, expires_at_dt)

    if result["matched_count"] == 0:
        raise HTTPException(status_code=404, detail="User not found")

    # Return JSON with expires_at as ISO string
    return {
        "matched_count": result["matched_count"],
        "modified_count": result["modified_count"],
        "user_id": user_id,
        "expires_at": payload.expires_at  # keep it as string
    }

# GET user by reset token
@router.get("/reset-token/{token}")
async def get_user_by_reset_token_endpoint(token: str):
    user_doc = await get_user_by_reset_token(token)
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    user_doc["_id"] = str(user_doc["_id"])
    return user_doc

# UPDATE user profile
@router.put("/{user_id}/profile")
async def update_user_profile_endpoint(user_id: str, payload: UpdateProfileRequest):
    updated_user = await update_user_profile(user_id, payload.update_fields)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user

# DELETE user
@router.delete("/{user_id}")
async def delete_user_endpoint(user_id: str):
    deleted_count = await delete_user(user_id)
    if deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"deleted_count": deleted_count, "message": "User deleted successfully"}

# UPDATE user profile picture
@router.put("/{user_id}/profile-pic")
async def update_user_profile_pic_endpoint(user_id: str, payload: UpdateProfilePicRequest):
    updated_user = await update_user_profile_pic(user_id, payload.new_pic_url)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user
