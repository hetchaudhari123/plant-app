from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime, timezone
from enum import Enum

class FarmSizeEnum(str, Enum):
    ONE_TO_FIVE = "1-5 acres"
    FIVE_TO_TWENTY = "5-20 acres"
    TWENTY_TO_FIFTY = "20-50 acres"
    FIFTY_TO_HUNDRED = "50-100 acres"
    HUNDRED_PLUS = "100+ acres"


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
    farm_size: Optional[FarmSizeEnum] = None  # 👈 updated to Enum
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None


    class Config:
        validate_by_name = True  # allows using "id" instead of "id"
        arbitrary_types_allowed = True 
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
