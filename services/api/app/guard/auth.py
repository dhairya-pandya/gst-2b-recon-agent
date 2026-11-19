from functools import lru_cache
from typing import Annotated, Any

import jwt
from fastapi import Depends, Header, HTTPException, Request

from app.config import Settings

ASYMMETRIC = {"ES256", "RS256"}


@lru_cache(maxsize=4)
def _jwk_client(jwks_url: str) -> jwt.PyJWKClient:
    # Keys are cached by the client; a new kid triggers one refetch.
    return jwt.PyJWKClient(jwks_url, cache_keys=True, lifespan=3600)


def jwks_url_for(supabase_url: str) -> str:
    return f"{supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json" if supabase_url else ""


def decode_token(token: str, secret: str, jwks_url: str = "") -> dict[str, Any]:
    """Verify a Supabase session token.

    Projects on signing keys issue ES256/RS256 tokens checked against the project JWKS.
    Legacy projects issue HS256 tokens checked against the shared JWT secret.
    """
    try:
        alg = jwt.get_unverified_header(token).get("alg")
        if alg in ASYMMETRIC:
            if not jwks_url:
                raise HTTPException(status_code=401, detail="invalid token")
            key: Any = _jwk_client(jwks_url).get_signing_key_from_jwt(token).key
            return jwt.decode(token, key, algorithms=[alg], audience="authenticated")
        if alg == "HS256" and secret:
            return jwt.decode(token, secret, algorithms=["HS256"], audience="authenticated")
    except (jwt.PyJWTError, jwt.PyJWKClientError) as exc:
        raise HTTPException(status_code=401, detail="invalid token") from exc
    raise HTTPException(status_code=401, detail="invalid token")


def current_user(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing bearer token")
    settings: Settings = request.app.state.settings
    claims = decode_token(
        authorization.removeprefix("Bearer "),
        settings.supabase_jwt_secret,
        jwks_url_for(settings.supabase_url),
    )
    sub = claims.get("sub")
    if not isinstance(sub, str):
        raise HTTPException(status_code=401, detail="invalid token")
    return sub


CurrentUser = Annotated[str, Depends(current_user)]
