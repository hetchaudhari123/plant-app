from uuid import uuid4
from utils.security_utils import hash_password, verify_password
from fastapi import HTTPException, Response, status, Request
from datetime import datetime, timedelta, timezone, timedelta
from jose import jwt, JWTError, ExpiredSignatureError
from config.config import settings
from pydantic import EmailStr

from utils.otp_utils import generate_secure_otp
from utils.email_utils import send_email
from utils.jinja_env import jinja_env
from jinja2 import Environment, FileSystemLoader, select_autoescape
import db.connections as db_conn

from services.profile_service import get_user_by_id

import secrets
from fastapi.templating import Jinja2Templates
from utils.auth_utils import create_access_token, create_refresh_token

async def send_otp(
    email: str,
    user_id: str = None,
    email_template: str = "email_signup.html",
    purpose: str = None
):
    """
    Generate a unique OTP for the given email, store it in OTP collection,
    and send it via email using a Jinja2 HTML template.
    """

    # 1) Remove any existing OTPs for this email
    await db_conn.otps_collection.delete_many({"email": email})

    # 2) Generate a secure 6-digit OTP
    MAX_ATTEMPTS = 10
    otp_code = None
    for _ in range(MAX_ATTEMPTS):
        candidate = generate_secure_otp(length=6)
        otp_doc = await db_conn.otps_collection.find_one({"otp": candidate})
        if otp_doc is None:
            otp_code = candidate
            break
    else:
        raise Exception("Failed to generate a unique OTP after 10 attempts")

    # 3) Prepare OTP document
    otp_doc = {
        "email": email,
        "otp": otp_code,
    }
    if user_id:
        otp_doc["user_id"] = user_id
    if purpose:
        otp_doc["purpose"] = purpose

    # 4) Insert into MongoDB
    await db_conn.otps_collection.insert_one(otp_doc)

    # 5) Render email template
    template = jinja_env.get_template(email_template)
    body = template.render(
        email=email,
        otp=otp_code,
        expires=settings.OTP_EXPIRE_MINUTES
    )

    # 6) Send OTP email
    subject = "Verify Your Email 🌱"
    await send_email(
        to_email=email,
        subject=subject,
        body=body,
        is_html=True
    )

    return {"message": "OTP sent successfully", "email": email}



async def signup_user(email: EmailStr, first_name: str, last_name: str, password: str, confirm_password: str, otp_input: str):

    # 0) Validate password confirmation
    if password != confirm_password:
        raise HTTPException(
            status_code=400,
            detail="Password and confirm password do not match"
        )
    

    existing = await db_conn.users_collection.find_one({"email": email})
    if existing:
        raise ValueError("User with this email already exists")

    # Fetch OTP from DB for this email
    otp_entry = await db_conn.otps_collection.find_one({"email": email, "otp": otp_input})

    if not otp_entry:
        raise HTTPException(status_code=400, detail="Invalid OTP")



    # Hash the password
    password_hash = hash_password(password)

    # Build display_name
    display_name = f"{first_name} {last_name}"

    # Generate profile picture URL (DiceBear initials avatar)
    profile_pic_url = f"https://api.dicebear.com/5.x/initials/svg?seed={first_name}%20{last_name}"



    user_doc = {
        "id": str(uuid4()),
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "password_hash": password_hash,
        "created_at": datetime.now(timezone.utc).isoformat(),  # serialize datetime
        "profile_pic_url": profile_pic_url,
        "last_login": None
    }



    await db_conn.users_collection.insert_one(user_doc)


    # Remove password before returning
    user_doc.pop("password_hash")

    # 10) Delete OTP after successful signup
    await db_conn.otps_collection.delete_many({"email": email})
    

        
    env = Environment(
        loader=FileSystemLoader("templates"),
        autoescape=select_autoescape(["html", "xml"])
    )
    template = env.get_template("email_welcome.html")

    # Send welcome email WITH OTP
    html_content = template.render(
        display_name=display_name
    )

    # Send the email
    await send_email(
        to_email=email,
        subject="Welcome to Plant App 🌱",
        body=html_content,
        is_html=True
    )

    return {
        "id": user_doc["id"],
        "email": user_doc["email"],
        "first_name": first_name,
        "last_name": last_name,
        "profile_pic_url": profile_pic_url
    }








async def login_user(email: EmailStr, password: str, response: Response):
    # 1) Find user
    user = await db_conn.users_collection.find_one({"email": email})

    if not user:
        raise HTTPException(status_code=404, detail="User with the given email not found")

    # 2) Verify password
    if not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Passwords do not match")

    # 3) Create tokens with token_version
    now = datetime.now(timezone.utc)
    token_version = user.get("token_version", 0)


    access_token = create_access_token(str(user["id"]), token_version)


    refresh_token = create_refresh_token(str(user["id"]), token_version)



    # 4) Store tokens in HttpOnly cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,   # ⚠️ set False if developing without HTTPS
        samesite="none",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    # 5) Remove sensitive field
    user.pop("password_hash", None)
    return user



async def change_password(user_id: str, old_password: str, new_password: str, confirm_password: str, response: Response):
    # 1) Find user by id
    user = await db_conn.users_collection.find_one({"id": user_id})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2) Verify old password
    if not verify_password(old_password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Old password is incorrect")

    # 3) Check new password and confirmation match
    if new_password != confirm_password:
        raise HTTPException(status_code=400, detail="New password and confirm password do not match")

    # 4) Hash the new password
    new_password_hash = hash_password(new_password)

    # 5) Atomically update password and increment token_version, return updated document
    updated_user = await db_conn.users_collection.find_one_and_update(
        {"id": user_id},
        {
            "$set": {"password_hash": new_password_hash},
            "$inc": {"token_version": 1}  # increment token_version
        },
        return_document=True  # returns the updated document
    )

    new_token_version = updated_user["token_version"]

    # 6) Remove old cookies
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    # 7) Create new tokens for current session
    now = datetime.now(timezone.utc)
    access_token = create_access_token(user_id, new_token_version)


    refresh_token = create_refresh_token(user_id, new_token_version)
    # 8) Set new cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )




async def reset_password_token(email: EmailStr):
    templates = Jinja2Templates(directory="templates")

    # 1) Find user by email
    user = await db_conn.users_collection.find_one({"email": email})


    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # 2) Generate secure random token
    token = secrets.token_urlsafe(32)


    # 3) Compute new expiry time
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.RESET_PASSWORD_TOKEN_EXPIRY_MINUTES
    )

    # 4) Remove any old token and set the new one

    await db_conn.users_collection.update_one(
        {"id": user["id"]},
        {
            "$set": {
                "reset_token": token,
                "reset_token_expires_at": expires_at
            }
        }
    )    


    # 5) Construct reset URL
    reset_url = f"{settings.FRONTEND_URL}/update-password/{token}"

    # 6) Render HTML email template
    template = templates.get_template("email_forget_password.html")
    body = template.render(
        user_name=user.get("first_name", ""),
        reset_link=reset_url,
        current_year=datetime.now().year
    )

    # 7) Send email
    subject = "Reset Your Password"
    await send_email(to_email=email, subject=subject, body=body)





async def reset_password(token: str, password: str, confirm_password: str):
    # 1) Validate confirm password
    if password != confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )

    # 2) Find user by reset token
    user = await db_conn.users_collection.find_one({"reset_token": token})

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token"
        )

    
    

    expires_at = user.get("reset_token_expires_at")

    if expires_at is not None:
        if isinstance(expires_at, str):
            # Parse ISO string back to datetime
            expires_at = datetime.fromisoformat(expires_at)

        if expires_at.tzinfo is None:
            # Make it UTC-aware
            expires_at = expires_at.replace(tzinfo=timezone.utc)

    if not expires_at or expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Reset token expired")

    # 4) Hash the new password
    hashed_password = hash_password(password)

    # 5) Update password & remove reset token
    await db_conn.users_collection.find_one_and_update(
            {"id": user["id"]},
            {
                "$set": {"password_hash": hashed_password},
                "$inc": {"token_version": 1}  # increment token_version
            },
            return_document=True  # returns the updated document
        )

    await db_conn.users_collection.update_one(
        {"id": user["id"]},
        {
            "$set": {
                "reset_token": None,
                "reset_token_expires_at": None
            }
        }
    )





async def refresh_access_token(request: Request, response: Response):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")

    try:
        payload = jwt.decode(refresh_token, settings.REFRESH_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid refresh token payload")

        user_doc = await db_conn.users_collection.find_one({"id": user_id})
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")

        # create new tokens
        # 7) Create new tokens for current session
        current_token_version = user_doc.get("token_version", 0)
        now = datetime.now(timezone.utc)


        new_access_token = create_access_token(user_id, current_token_version)


        new_refresh_token = create_refresh_token(user_id, current_token_version)


        # set cookies
        response.set_cookie(
            key="access_token",
            value=new_access_token,
            httponly=True,
            secure=True,
            samesite="none",
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,

        )
        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            secure=True,
            samesite="none",
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,

        )

        return {"accessToken": new_access_token}

    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    


async def logout_user(response: Response):
    """
    Logout the user by clearing access and refresh token cookies.
    """
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")



async def generate_otp_token(user_id: str, email: EmailStr, new_email: EmailStr):
    """
    Generate a secure OTP token tied to a user and store it in the otp_tokens collection.
    """
    # 1) Verify user exists
    user = await db_conn.users_collection.find_one({"id": user_id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # 2) Generate secure random token
    token = secrets.token_urlsafe(32)

    # 3) Compute expiry time for token
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.OTP_EXPIRE_MINUTES  # e.g. 10 minutes
    )

    # 4) Insert new OTP token in collection
    otp_token_doc = {
        "user_id": user_id,
        "email": email,
        "new_email": new_email,
        "token": token,
        "created_at": datetime.now(timezone.utc),
        "expires_at": expires_at,
        "resend_count": 0
    }

    await db_conn.otp_tokens_collection.insert_one(otp_token_doc)

    return {
        "otp_token": token,
        "expires_at": expires_at
    }






async def resend_email_change_otp(user_id: str):
    """
    Service function that:
     Finds the latest valid otp_token for email change
     Increments resend_count (checks limit)
     Generates and sends a new OTP using send_otp
    """
    # Find latest valid otp_token
    token_doc = await db_conn.otp_tokens_collection.find_one(
        {"user_id": user_id, "expires_at": {"$gt": datetime.now(timezone.utc)}},
        sort=[("created_at", -1)]
    )

    if not token_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="OTP token not found or expired. Please restart email change process."
        )

    # Increment resend_count
    resend_count = token_doc.get("resend_count", 0) + 1

    if resend_count > settings.RESEND_OTP_LIMIT:
        # Remove token from DB
        await db_conn.otp_tokens_collection.delete_one({"_id": token_doc["_id"]})
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Resend OTP limit exceeded. Please restart email change process."
        )

    # Update resend_count in DB
    await db_conn.otp_tokens_collection.update_one(
        {"_id": token_doc["_id"]},
        {"$set": {"resend_count": resend_count}}
    )

    # Send new OTP using helper
    await send_otp(token_doc["new_email"], user_id=user_id, email_template="email_change.html", purpose="email_change")

    return {"message": "OTP resent successfully", "resend_count": resend_count}