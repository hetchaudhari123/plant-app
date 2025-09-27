from fastapi import Depends, Request, Response, HTTPException, status
from config.config import settings

from utils.auth_utils import (
    decode_access_token,
    decode_refresh_token,
    create_access_token,
    create_refresh_token,
    TokenPayload,
)

async def require_user(request: Request, response: Response):
    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")

    if not access_token or not refresh_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Try access token first
    try:
        payload: TokenPayload = decode_access_token(access_token)
        request.state.user_id = payload.sub
        return payload.sub
    except HTTPException:
        # Access token invalid/expired → try refresh
        try:
            refresh_payload: TokenPayload = decode_refresh_token(refresh_token)
        except HTTPException:
            raise HTTPException(status_code=401, detail="Session expired")

        # Issue new tokens using token_version from refresh token
        new_access = create_access_token(
            user_id=refresh_payload.sub,
            token_version=refresh_payload.token_version,
        )
        new_refresh = create_refresh_token(
            user_id=refresh_payload.sub,
            token_version=refresh_payload.token_version,
        )

        # Attach new cookies
        response.set_cookie(
            "access_token", new_access,
            httponly=True, secure=True, samesite="none", max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,

        )
        response.set_cookie(
            "refresh_token", new_refresh,
            httponly=True, secure=True, samesite="none", max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        )

        request.state.user_id = refresh_payload.sub
        return refresh_payload.sub
