from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, timezone, timedelta
from typing import Optional
from enum import Enum


class OTPPurpose(str, Enum):
    signup = "signup"
    reset_password = "reset_password"
    email_change = "email_change"


class OTP(BaseModel):
    email: EmailStr
    otp: str
    user_id: Optional[str] = None
    purpose: OTPPurpose = OTPPurpose.signup
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
        + timedelta(minutes=5)  # or settings.OTP_EXPIRE_MINUTES
    )

    class Config:
        validate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {datetime: lambda dt: dt.isoformat()}
