from fastapi import Depends, Request, Response, HTTPException, status
from config.config import settings
from pydantic import BaseModel
from utils.auth_utils import (
    decode_access_token,
    decode_refresh_token,
    create_access_token,
    create_refresh_token,
    TokenPayload,
)
from typing import Optional



class AuthUser(BaseModel):
    id: str
    token_version: int


async def require_user(request: Request, response: Response) -> AuthUser:
    access_token: Optional[str] = request.cookies.get("access_token")
    refresh_token: Optional[str] = request.cookies.get("refresh_token")

    if not access_token and not refresh_token:
        # Neither token is present → user is unauthenticated
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload: Optional[TokenPayload] = None

    # Try to decode access token if it exists
    if access_token:
        try:
            payload = decode_access_token(access_token)
        except HTTPException:
            payload = None  # invalid/expired, will try refresh token

    # If access token missing or invalid, use refresh token
    if payload is None:
        if not refresh_token:
            raise HTTPException(status_code=401, detail="Session expired")

        try:
            refresh_payload: TokenPayload = decode_refresh_token(refresh_token)
        except HTTPException:
            raise HTTPException(status_code=401, detail="Session expired")

        # Issue new tokens using the refresh token
        new_access = create_access_token(user_id=refresh_payload.sub, token_version=refresh_payload.token_version)
        new_refresh = create_refresh_token(user_id=refresh_payload.sub, token_version=refresh_payload.token_version)

        response.set_cookie(
            "access_token", new_access, httponly=True, secure=True, samesite="none",
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        response.set_cookie(
            "refresh_token", new_refresh, httponly=True, secure=True, samesite="none",
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        )

        payload = refresh_payload  # now payload has valid user info

    # Create AuthUser and attach to request state
    user = AuthUser(id=payload.sub, token_version=payload.token_version)
    request.state.user = user
    return user
