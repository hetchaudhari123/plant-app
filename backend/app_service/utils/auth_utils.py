from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from pydantic import BaseModel
from typing import Literal
from fastapi import HTTPException, status
from config.config import settings


# ------------------------------
# Token payload model
# ------------------------------
class TokenPayload(BaseModel):
    sub: str  # user_id
    type: Literal["access", "refresh"]  # token type
    token_version: int  # for forced invalidation
    exp: datetime  # timezone-aware expiry


# ------------------------------
# Create Access Token
# ------------------------------
def create_access_token(user_id: str, token_version: int) -> str:
    exp = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = TokenPayload(
        sub=user_id,
        type="access",
        token_version=token_version,
        exp=exp,
    )
    return jwt.encode(
        payload.model_dump(),
        settings.ACCESS_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


# ------------------------------
# Create Refresh Token
# ------------------------------
def create_refresh_token(user_id: str, token_version: int) -> str:
    exp = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload = TokenPayload(
        sub=user_id,
        type="refresh",
        token_version=token_version,
        exp=exp,
    )
    return jwt.encode(
        payload.model_dump(),
        settings.REFRESH_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


# ------------------------------
# Decode Access Token
# ------------------------------
def decode_access_token(token: str) -> TokenPayload:
    try:
        decoded = jwt.decode(
            token,
            settings.ACCESS_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        payload = TokenPayload(**decoded)
        if payload.type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
        )


# ------------------------------
# Decode Refresh Token
# ------------------------------
def decode_refresh_token(token: str) -> TokenPayload:
    try:
        decoded = jwt.decode(
            token,
            settings.REFRESH_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        payload = TokenPayload(**decoded)
        if payload.type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
