from uuid import uuid4
from utils.security_utils import hash_password, verify_password

from fastapi import HTTPException, Response, status
from datetime import datetime, timedelta, timezone, timedelta
from jose import jwt
from config.config import settings
from pydantic import EmailStr

from utils.otp_utils import generate_secure_otp
from utils.email_utils import send_email
from jinja2 import Environment, FileSystemLoader, select_autoescape


from crud_apis.users_api import get_user_by_email, create_user, get_user_by_id, update_user_password, update_reset_token, get_user_by_reset_token
import secrets
from fastapi.templating import Jinja2Templates
from crud_apis.otp_api import delete_otps_for_email, get_otp_by_code, create_otp, get_otp_by_email_and_code


async def send_otp(email: EmailStr):
    """
    Generate a unique OTP for the given email, store it in OTP collection,
    and send it via email using a Jinja2 HTML template.
    """

    # 1) Remove any existing OTPs for this email
    await delete_otps_for_email(email)

    # 2) Generate a secure 6-digit OTP
    otp_code = generate_secure_otp(length=6)

    # Ensure uniqueness across currently stored OTPs
    MAX_ATTEMPTS = 10
    for _ in range(MAX_ATTEMPTS):
        otp_code = generate_secure_otp(length=6)
        otp_doc = await get_otp_by_code(otp_code)
        if otp_doc is None:
            break
    else:
        raise Exception("Failed to generate a unique OTP after 10 attempts")


    # 3) Prepare OTP document
    otp_doc = {
        "email": email,
        "otp": otp_code
    }

    # 4) Insert into MongoDB
    await create_otp(otp_doc)

    # 5) Load Jinja2 template
    env = Environment(
        loader=FileSystemLoader("templates"),
        autoescape=select_autoescape(["html", "xml"])
    )
    template = env.get_template("email_signup.html")

    # 6) Render the template with dynamic content
    body = template.render(
        email=email,
        otp=otp_code,
        expires=settings.OTP_EXPIRE_MINUTES
    )

    # 7) Send OTP email
    subject = "Verify Your Email 🌱"
    await send_email(
        to_email=email,
        subject=subject,
        body=body,
        is_html=True
    )




async def signup_user(email: EmailStr, first_name: str, last_name: str, password: str, confirm_password: str, otp_input: str):

    # 0) Validate password confirmation
    if password != confirm_password:
        raise HTTPException(
            status_code=400,
            detail="Password and confirm password do not match"
        )
    

    existing = await get_user_by_email(email)
    if existing:
        raise ValueError("User with this email already exists")

    # Fetch OTP from DB for this email
    otp_entry = await get_otp_by_email_and_code(email, otp_input)
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



    await create_user(user_doc)

    # Remove password before returning
    user_doc.pop("password_hash")

    # 10) Delete OTP after successful signup
    await delete_otps_for_email(email)

        
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









async def login_user(email: EmailStr, password: str, response: Response):
    # 1) Find user
    user = await get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=401, detail="User with the given email not found")

    # 2) Verify password
    if not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Passwords do not match")

    # 3) Create tokens with token_version
    now = datetime.now(timezone.utc)
    token_version = user.get("token_version", 0)

    access_token = jwt.encode(
        {
            "sub": str(user["id"]),
            "type": "access",
            "token_version": token_version,
            "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        },
        settings.ACCESS_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    refresh_token = jwt.encode(
        {
            "sub": str(user["id"]),
            "type": "refresh",
            "token_version": token_version,
            "exp": now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        },
        settings.REFRESH_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

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




async def change_password(user_id: str, old_password: str, new_password: str, confirm_password: str, response: Response):
    # 1) Find user by id
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2) Verify old password
    if not verify_password(old_password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Old password is incorrect")

    # 3) Check new password and confirmation match
    if new_password != confirm_password:
        raise HTTPException(status_code=400, detail="New password and confirm password do not match")

    # 4) Hash the new password
    new_password_hash = hash_password(new_password)

    # 5) Atomically update password and increment token_version, return updated document
    updated_user = await update_user_password(user_id, new_password_hash)

    new_token_version = updated_user["token_version"]

    # 6) Remove old cookies
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    # 7) Create new tokens for current session
    now = datetime.now(timezone.utc)
    access_token = jwt.encode(
        {"sub": user_id, "type": "access", "token_version": new_token_version,
         "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)},
        settings.ACCESS_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    refresh_token = jwt.encode(
        {"sub": user_id, "type": "refresh", "token_version": new_token_version,
         "exp": now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)},
        settings.REFRESH_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

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
    user = await get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # 2) Generate secure random token
    token = secrets.token_hex(20)

    # 3) Compute new expiry time
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.RESET_PASSWORD_TOKEN_EXPIRY_MINUTES
    )

    # 4) Remove any old token and set the new one

    await update_reset_token(user["id"], token, expires_at)

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
    user = await get_user_by_reset_token(token)
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
    await update_user_password(user["id"], hashed_password)

    await update_reset_token(user["id"], token=None, expires_at=None)



