from fastapi import HTTPException, Response, UploadFile, File
from db.connections import users_collection, predictions_collection, jobs_collection, otps_collection 
import cloudinary.uploader
from utils.security_utils import verify_password
from utils.otp_utils import generate_secure_otp
from datetime import datetime, timedelta, timezone
import uuid
from db.connections import users_collection, otps_collection
from utils.email_utils import send_email
from config.config import settings
from models.otp import OTPPurpose
from jinja2 import Environment, FileSystemLoader, select_autoescape





async def update_profile_name(user_id: str, first_name: str = None, last_name: str = None):
    """
    Update a user's first name and/or last name.
    Only update profile_pic_url if it is still the default DiceBear avatar.
    """
    # 1) Fetch user
    user = await users_collection.find_one({"id": user_id})
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
    await users_collection.update_one(
        {"id": user_id},
        {"$set": update_fields}
    )

    # 5) Return updated user (without password_hash)
    updated_user = await users_collection.find_one({"id": user_id}, {"password_hash": 0})


async def delete_account(user_id: str, response: Response):
    """
    Delete a user's account and related data.
    """

    # 1) Check if user exists
    user = await users_collection.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2) Delete the user
    await users_collection.delete_one({"id": user_id})

    # 3) Delete related data (cascade cleanup)
    await predictions_collection.delete_many({"user_id": user_id})
    await jobs_collection.delete_many({"user_id": user_id})
    await otps_collection.delete_many({"email": user["email"]})


    # 4) Clear authentication cookies
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")






async def update_profile_picture(user_id: str, file: UploadFile = File(...)):
    # 1) Check if user exists
    user = await users_collection.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2) Upload the file to Cloudinary
    try:
        upload_result = cloudinary.uploader.upload(
            file.file,
            folder="plant_app/profile_pics",
            overwrite=True,
            resource_type="image"
        )
        new_pic_url = upload_result["secure_url"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cloudinary upload failed: {str(e)}")

    # 3) Update MongoDB with the new profile picture
    update_result = await users_collection.update_one(
        {"id": user_id},
        {"$set": {"profile_pic": new_pic_url}}
    )

    if update_result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Profile picture update failed")




async def request_email_change(user_id: str, new_email: str, current_password: str):
    """
    Request email change by validating password and sending OTP to new email.
    """


    # 0) Delete any existing OTPs for this user and purpose
    await otps_collection.delete_many({
        "user_id": user_id
    })

    # 1) Find the user
    user = await users_collection.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2) Validate password
    if not verify_password(current_password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Current password is incorrect")

    # 3) Generate secure 6-digit OTP
    otp_code = generate_secure_otp(length=6)

    # 4) Create OTP entry
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)

    otp_entry = {
        "user_id": user_id,
        "email": new_email,
        "otp": otp_code,
        "purpose":OTPPurpose.email_change,
        "expires_at": expires_at,
    }

    await otps_collection.insert_one(otp_entry)

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



async def confirm_email_change(user_id: str, new_email: str, otp_code: str):
    """
    Confirm the email change by validating the OTP and updating the user's email.
    """

    # 1) Find OTP entry
    otp_entry = await otps_collection.find_one({
        "user_id": user_id,
        "email": new_email,
        "otp": otp_code,
        "purpose": OTPPurpose.email_change.value
    })

    if not otp_entry:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    # 2) Mark OTP as verified
    await otps_collection.delete_one({"_id": otp_entry["_id"]})

    # 3) Update user's email in users_collection
    result = await users_collection.update_one(
        {"id": user_id},
        {"$set": {"email": new_email}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Failed to update email")
