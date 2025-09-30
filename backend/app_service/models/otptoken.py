from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, timezone, timedelta
from typing import Optional

class OTPToken(BaseModel):
    user_id: str
    email: EmailStr
    new_email: EmailStr
    token: str  # randomly generated string/UUID
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc) + timedelta(minutes=10)
    )
    resend_count: int = 0

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
