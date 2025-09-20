from fastapi import HTTPException, Response, UploadFile, File
from utils.security_utils import verify_password
from utils.otp_utils import generate_secure_otp
from datetime import datetime, timedelta, timezone
from utils.email_utils import send_email
from config.config import settings
from jinja2 import Environment, FileSystemLoader, select_autoescape
from crud_apis.predictions_api import delete_predictions_by_user
import cloudinary
import cloudinary.uploader

from crud_apis.users_api import get_user_by_email, create_user, get_user_by_id, update_user_password, update_reset_token, get_user_by_reset_token, update_user_profile, delete_user, update_user_profile_pic
from crud_apis.jobs_api import delete_jobs_by_user

from crud_apis.otp_api import delete_otps_for_email, delete_otps_by_user, create_otp, get_otp_for_email_change, delete_otps_by_user, delete_otps_for_email


async def update_profile_name(user_id: str, first_name: str = None, last_name: str = None):
    """
    Update a user's first name and/or last name.
    Only update profile_pic_url if it is still the default DiceBear avatar.
    """
    # 1) Fetch user
    user = await get_user_by_id(user_id)
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
    updated_user = await update_user_profile(user_id, update_fields)


async def delete_account(user_id: str, response: Response):
    """
    Delete a user's account and related data.
    """

    # 1) Check if user exists
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2) Delete the user
    await delete_user(user_id)

    # 3) Delete related data (cascade cleanup)
    await delete_predictions_by_user(user_id)
    await delete_jobs_by_user(user_id)
    await delete_otps_for_email(user["email"])


    # 4) Clear authentication cookies
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")





async def update_profile_picture(user_id: str, file: UploadFile = File(...)):
    # 1) Check if user exists
    user = await get_user_by_id(user_id)
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
    update_result = await update_user_profile_pic(user_id, new_pic_url)
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
    await delete_otps_by_user(user_id)
    # 1) Find the user
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2) Validate password
    if not verify_password(current_password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Current password is incorrect")

    # 3) Generate secure 6-digit OTP
    otp_code = generate_secure_otp(length=6)

    otp_entry = {
        "user_id": user_id,
        "email": new_email,
        "otp": otp_code,
        "purpose":"email_change",
    }

    await create_otp(otp_entry)

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
    otp_entry = await get_otp_for_email_change(user_id, new_email, otp_code)

    if not otp_entry:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    # 2) Mark OTP as verified
    await delete_otps_for_email(new_email)
    

    # 3) Update user's email in users_collection
    update_fields = {"email": new_email}
    result = await update_user_profile(user_id, update_fields)


    # if result.modified_count == 0:
    if not result or "id" not in result:
        raise HTTPException(status_code=400, detail="Profile picture update failed")
