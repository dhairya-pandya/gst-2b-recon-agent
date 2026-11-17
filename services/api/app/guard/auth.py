from typing import Annotated, Any

import jwt
from fastapi import Depends, Header, HTTPException, Request

from app.config import Settings


def decode_token(token: str, secret: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, secret, algorithms=["HS256"], audience="authenticated")
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="invalid token") from exc


def current_user(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing bearer token")
    settings: Settings = request.app.state.settings
    claims = decode_token(authorization.removeprefix("Bearer "), settings.supabase_jwt_secret)
    sub = claims.get("sub")
    if not isinstance(sub, str):
        raise HTTPException(status_code=401, detail="invalid token")
    return sub


CurrentUser = Annotated[str, Depends(current_user)]
