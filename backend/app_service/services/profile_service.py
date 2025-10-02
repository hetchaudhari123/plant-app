from fastapi import HTTPException, Response, UploadFile, File, Depends
from utils.security_utils import verify_password
from utils.otp_utils import generate_secure_otp
from datetime import datetime, timedelta, timezone
from utils.email_utils import send_email
from config.config import settings
from jinja2 import Environment, FileSystemLoader, select_autoescape
import cloudinary
import cloudinary.uploader
from models.user import User
from models.prediction import Prediction
import db.connections as db_conn
from typing import List
from schemas.UserDashboardResponseSchema import UserDashboardResponse
from collections import Counter
from pymongo import ReturnDocument
from pydantic import BaseModel
from passlib.context import CryptContext

async def update_profile_name(user_id: str, first_name: str = None, last_name: str = None):
    """
    Update a user's first name and/or last name.
    Only update profile_pic_url if it is still the default DiceBear avatar.
    """
    # 1) Fetch user
    user = await db_conn.users_collection.find_one({"id": user_id})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2) Prepare update fields
    update_fields = {}

    if first_name is not None:
        update_fields["first_name"] = first_name

    if last_name is not None:
        update_fields["last_name"] = last_name

    # 3) If either name updated, populate the update_fields
    if "first_name" in update_fields or "last_name" in update_fields:
        new_first = update_fields.get("first_name", user["first_name"])
        new_last = update_fields.get("last_name", user["last_name"])


        # Update profile picture only if user has DiceBear avatar
        if "api.dicebear.com" in user.get("profile_pic_url", ""):
            update_fields["profile_pic_url"] = (
                f"https://api.dicebear.com/5.x/initials/svg?seed={new_first}%20{new_last}"
            )

    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    # 4) Perform update
    await db_conn.users_collection.find_one_and_update(
        {"id": user_id},
        {"$set": update_fields},
        return_document=True  # returns the updated document
    )


async def delete_account(user_id: str, password: str, response: Response):
    """
    Delete a user's account and related data after verifying password.
    """
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    # 1) Check if user exists
    user = await db_conn.users_collection.find_one({"id": user_id})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2) Verify password
    if "password_hash" not in user:
        raise HTTPException(status_code=400, detail="User account has no password set")
    
    # Check if the provided password matches the stored hash
    if not pwd_context.verify(password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect password")

    # 3) Delete the user
    await db_conn.users_collection.delete_one({"id": user_id})

    # 4) Delete related data (cascade cleanup)
    await db_conn.predictions_collection.delete_many({"user_id": user_id})
    # await delete_jobs_by_user(user_id)
    await db_conn.otps_collection.delete_many({"email": user["email"]})

    # 5) Clear authentication cookies
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")





async def update_profile_picture(user_id: str, file: UploadFile = File(...)):
    # 1) Check if user exists
    user = await db_conn.users_collection.find_one({"id": user_id})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2) Upload to Cloudinary
    try:
        file.file.seek(0)  
        upload_result = cloudinary.uploader.upload(
            file.file,
            folder="plant_app/profile_pics",
            overwrite=True,
            resource_type="image"
        )
        new_pic_url = upload_result["secure_url"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cloudinary upload failed: {str(e)}")

    # 3) Update backend
    update_result = await db_conn.users_collection.find_one_and_update(
        {"id": user_id},
        {"$set": {"profile_pic_url": new_pic_url}},
        return_document=True  # returns the updated document
    )
    if not update_result or "id" not in update_result:
        raise HTTPException(status_code=400, detail="Profile picture update failed")

    # 4) Return a proper dict
    return {
        "message": "Profile picture updated successfully",
        "user_id": user_id,
        "new_pic_url": new_pic_url
    }




async def request_email_change(user_id: str, new_email: str, current_password: str):
    """
    Request email change by validating password and sending OTP to new email.
    """


    # 0) Delete any existing OTPs for this user and purpose
    await db_conn.otps_collection.delete_many({"user_id": user_id})

    # 1) Find the user
    user = await db_conn.users_collection.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2) Validate password
    if not verify_password(current_password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    # 3) Generate secure 6-digit OTP
    otp_code = generate_secure_otp(length=6)

    otp_entry = {
        "user_id": user_id,
        "email": new_email,
        "otp": otp_code,
        "purpose":"email_change",
    }

    await db_conn.otps_collection.insert_one(otp_entry)


    # 1) Set up Jinja2 environment (pointing to your templates folder)
    env = Environment(
        loader=FileSystemLoader("templates"),
        autoescape=select_autoescape(["html", "xml"])
    )

    # 2) Load the template
    template = env.get_template("email_change.html")

    # 3) Render the template with dynamic values
    body = template.render(
        display_name=user.get("first_name", "User"),
        otp=otp_code,
        expiry=settings.OTP_EXPIRE_MINUTES,  # or whatever config you have
    )

    # 7) Send OTP email (HTML)
    subject = "Confirm Your Email Change 🌱"
    await send_email(
        to_email=new_email,
        subject=subject,
        body=body,
        is_html=True
    )



async def confirm_email_change(user_id: str, old_email: str, new_email: str, otp_code: str):
    """
    Confirm the email change by validating the OTP (with old email)
    and updating the user's email to the new one.
    """

    # 1) Find OTP entry using old_email (not new_email)
    otp_entry = await db_conn.otps_collection.find_one({
        "user_id": user_id,
        "email": new_email,
        "otp": otp_code,
        "purpose": "email_change"
    })

    if not otp_entry:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    # 2) Mark OTP as verified (delete old OTPs tied to old_email)
    await db_conn.otps_collection.delete_many({"email": new_email})

    # 3) Update user's email in users_collection
    update_fields = {"email": new_email}
    result = await db_conn.users_collection.find_one_and_update(
        {"id": user_id, "email": old_email},  # also ensure the user had old_email
        {"$set": update_fields},
        return_document=True  # returns the updated document
    )

    if not result or "id" not in result:
        raise HTTPException(status_code=400, detail="Email update failed")

    return {"message": "Email updated successfully", "new_email": new_email}




async def get_user_by_id(user_id: str) -> dict:
    """
    Fetch user details by ID from the database and remove sensitive fields.
    """
    user_doc = await db_conn.users_collection.find_one({"id": user_id})
    
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")

    # Convert MongoDB document to User model
    user = User(**user_doc)

    # Prepare safe dictionary for response
    user_dict = user.model_dump(exclude={"password_hash", "reset_token", "reset_token_expires_at", "token_version"})
    
    return user_dict



async def get_user_details(user_id: str) -> dict:
    """
    Fetch user details by ID from the database and remove sensitive fields.
    """
    user_doc = await db_conn.users_collection.find_one({"id": user_id})
    
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")

    # Convert MongoDB document to User model
    user = User(**user_doc)

    # Prepare safe dictionary for response
    user_dict = user.model_dump(exclude={"password_hash", "reset_token", "reset_token_expires_at", "token_version"})
    
    return user_dict



async def get_user_dashboard(user_id: str) -> UserDashboardResponse:
    """
    Fetch user and predictions from DB and build a dashboard summary.
    """

    # --- Fetch user ---
    user_doc = await db_conn.users_collection.find_one({"id": user_id})
    if not user_doc:
        raise ValueError(f"User with id {user_id} not found")

    user = User(**user_doc)

    # --- Fetch predictions ---
    prediction_docs = await db_conn.predictions_collection.find({"user_id": user_id}).to_list(length=None)
    predictions = [Prediction(**doc) for doc in prediction_docs]

    # --- Calculate stats ---
    total_analyses = len(predictions)

    issues_detected = sum(
        1 for p in predictions
        if p.disease and p.disease.lower() != "healthy"
    )

    healthy_crops = sum(
        1 for p in predictions
        if p.disease and p.disease.lower() == "healthy"
    )

    crops_monitored_count = len(set(p.crop for p in predictions if p.crop))  # count of unique crops
    
    return UserDashboardResponse(
        user_id=user.id,
        total_analyses=total_analyses,
        issues_detected=issues_detected,
        healthy_crops=healthy_crops,
        crops_monitored=crops_monitored_count,  
    )



async def get_primary_crops_for_user(user_id: str, top_n: int = 3) -> List[str]:
    """
    Fetch predictions from DB for the given user and return top N primary crops.
    """
    # Fetch all predictions for this user
    prediction_docs = await db_conn.predictions_collection.find({"user_id": user_id}).to_list(length=None)
    predictions = [Prediction(**doc) for doc in prediction_docs]

    # Filter out predictions with empty crop
    crops = [p.crop for p in predictions if p.crop]

    # Count occurrences
    crop_counts = Counter(crops)

    # Get top N crops
    primary_crops = [crop for crop, _ in crop_counts.most_common(top_n)]
    return primary_crops




async def update_farm_size(user_id: str, farm_size: str) -> dict:
    """
    Update the farm size for a given user.

    Args:
        user_id (str): ID of the user whose farm size will be updated.
        farm_size (str): New farm size (e.g., "1-5 acres").

    Returns:
        dict: Updated user document.
    """
    # Update the farm_size field for the user
    updated_user = await db_conn.users_collection.find_one_and_update(
        {"id": user_id},
        {"$set": {"farm_size": farm_size}},
        return_document=ReturnDocument.AFTER  # returns the updated document
    )

    if not updated_user:
        raise ValueError(f"User with id {user_id} not found")

    return updated_user



