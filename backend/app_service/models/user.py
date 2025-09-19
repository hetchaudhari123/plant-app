from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime, timezone, timedelta
from config.config import settings

class User(BaseModel):
    id: str
    email: EmailStr
    token_version: int = 0
    first_name: str
    last_name: str
    reset_token: Optional[str] = None
    reset_token_expires_at: Optional[datetime] = None  # NEW FIELD
    profile_pic_url: Optional[str] = None
    password_hash: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None



    class Config:
        validate_by_name = True  # allows using "id" instead of "id"
        arbitrary_types_allowed = True 
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
