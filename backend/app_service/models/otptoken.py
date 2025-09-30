from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, timezone, timedelta
from typing import Optional

class OTPToken(BaseModel):
    user_id: str
    email: EmailStr
    new_email: Optional[EmailStr] = None  # Make optional since signup won't have this
    token: str  # randomly generated string/UUID
    otp_type: str = "email_change"  # Add type field: "email_change", "signup", etc.
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc) + timedelta(minutes=10)
    )
    resend_count: int = 0
    pending_data: Optional[dict] = None  # For signup: first_name, last_name, password_hash, profile_pic_url

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }