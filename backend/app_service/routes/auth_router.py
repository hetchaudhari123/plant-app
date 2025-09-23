from fastapi import APIRouter, Response, Body
from pydantic import BaseModel, EmailStr
from services.auth_service import send_otp, signup_user, login_user, change_password, reset_password, reset_password_token

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
    user_id: str
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
    await signup_user(
        email=payload.email,
        first_name=payload.first_name,
        last_name=payload.last_name,
        password=payload.password,
        confirm_password=payload.confirm_password,  # ✅ add this
        otp_input=payload.otp_input
    )
    return {"message": "User signed up successfully"}

@router.post("/login", summary="Login user and return access token")
async def route_login(payload: LoginSchema, response: Response):
    await login_user(email=payload.email, password=payload.password, response=response)
    return {"message": "Login successful"}

@router.post("/change-password", summary="Change password for logged-in user")
async def route_change_password(payload: ChangePasswordSchema, response: Response):
    await change_password(
        user_id=payload.user_id,
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
