from fastapi import APIRouter, Response, Body, Depends, Request, HTTPException, status
from pydantic import BaseModel, EmailStr
from services.auth_service import send_otp, signup_user, login_user, change_password, reset_password, reset_password_token, refresh_access_token, logout_user, generate_otp_token, resend_email_change_otp
from dependencies.auth import require_user

router = APIRouter()

# --------------------
# Request Schemas
# --------------------


class OTPRequest(BaseModel):
    email: EmailStr


class SignupSchema(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    password: str
    confirm_password: str  # ✅ add this
    otp_input: str

class LoginSchema(BaseModel):
    email: EmailStr
    password: str

class ChangePasswordSchema(BaseModel):
    old_password: str
    new_password: str
    confirm_password: str


class ResetPasswordTokenSchema(BaseModel):
    email: EmailStr

class ResetPasswordSchema(BaseModel):
    token: str
    password: str
    confirm_password: str

# --------------------
# Routes
# --------------------


@router.post("/send-otp")
async def send_otp_endpoint(request: OTPRequest):
    await send_otp(request.email)
    return {"message": "OTP sent successfully"}


@router.post("/signup", summary="Signup a new user with OTP verification")
async def route_signup(payload: SignupSchema = Body(...)):
    user = await signup_user(
        email=payload.email,
        first_name=payload.first_name,
        last_name=payload.last_name,
        password=payload.password,
        confirm_password=payload.confirm_password,  # ✅ add this
        otp_input=payload.otp_input
    )
    return {
        "message": "User signed up successfully",
        "user": user
    }

@router.post("/login", summary="Login user and return access token")
async def route_login(payload: LoginSchema, response: Response):
    user = await login_user(email=payload.email, password=payload.password, response=response)
    return {
        "message": "Login successful",
        "user": {
            "id": str(user["id"]),
            "email": user["email"],
            "first_name": user.get("first_name"),
            "last_name": user.get("last_name"),
            "profile_pic_url": user.get("profile_pic_url")
        }
    }


@router.post("/change-password", summary="Change password for logged-in user")
async def route_change_password(payload: ChangePasswordSchema, response: Response, user = Depends(require_user)):
    await change_password(
        user_id=user.id,
        old_password=payload.old_password,
        new_password=payload.new_password,
        confirm_password=payload.confirm_password,
        response=response
    )
    return {"message": "Password changed successfully"}






@router.post("/reset-password-token", summary="Generate password reset token")
async def route_reset_password_token(payload: ResetPasswordTokenSchema):
    await reset_password_token(email=payload.email)
    return {"message": "Password reset link sent to your email"}


@router.post("/reset-password", summary="Reset password using token")
async def route_reset_password(payload: ResetPasswordSchema):
    await reset_password(
        token=payload.token,
        password=payload.password,
        confirm_password=payload.confirm_password
    )
    return {"message": "Password has been reset successfully"}


@router.post("/refresh", summary="Refresh access token using refresh token")
async def route_refresh_access_token(request: Request, response: Response):
    """
    Refresh the access token using the refresh token stored in cookies.
    Sets new access and refresh tokens in HttpOnly cookies.
    """
    return await refresh_access_token(request, response)


@router.post("/logout", summary="Logout user by clearing cookies")
async def route_logout(response: Response):
    """
    Logout endpoint. Clears HttpOnly cookies for access and refresh tokens.
    """
    await logout_user(response)
    return {"message": "Logged out successfully"}

class OTPTokenRequest(BaseModel):
    email: EmailStr 
    new_email: EmailStr

@router.post("/otp-token", summary="Generate OTP token for email change")
async def route_generate_otp_token(payload: OTPTokenRequest, user = Depends(require_user)):
    """
    Generate an OTP token for a given user.
    This token can later be used to resend OTPs without requiring the password again.
    """
    return await generate_otp_token(user_id=user.id, email=payload.email, new_email=payload.new_email)






@router.post("/otp-token/resend-otp", summary="Resend OTP for email change")
async def route_resend_otp(user=Depends(require_user)):
    """
    Resend OTP for email change.
    Backend finds the user's OTP token, increments resend_count, 
    and sends a new OTP.
    """
    return await resend_email_change_otp(user_id=user.id)