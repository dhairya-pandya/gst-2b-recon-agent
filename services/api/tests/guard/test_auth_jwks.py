import time
from types import SimpleNamespace
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi import HTTPException

from app.guard import auth

KEY = ec.generate_private_key(ec.SECP256R1())
OTHER = ec.generate_private_key(ec.SECP256R1())


def _es256(key: Any, aud: str = "authenticated") -> str:
    now = int(time.time())
    claims = {"sub": "user-1", "aud": aud, "exp": now + 300, "iat": now}
    return jwt.encode(claims, key, algorithm="ES256", headers={"kid": "k1"})


@pytest.fixture(autouse=True)
def fake_jwks(monkeypatch: pytest.MonkeyPatch) -> None:
    client = SimpleNamespace(
        get_signing_key_from_jwt=lambda _t: SimpleNamespace(key=KEY.public_key())
    )
    monkeypatch.setattr(auth, "_jwk_client", lambda _url: client)


def test_es256_token_verified_against_jwks() -> None:
    claims = auth.decode_token(
        _es256(KEY), "", "https://x.supabase.co/auth/v1/.well-known/jwks.json"
    )
    assert claims["sub"] == "user-1"


def test_es256_signed_by_other_key_rejected() -> None:
    with pytest.raises(HTTPException) as e:
        auth.decode_token(_es256(OTHER), "", "https://x/jwks.json")
    assert e.value.status_code == 401


def test_es256_wrong_audience_rejected() -> None:
    with pytest.raises(HTTPException):
        auth.decode_token(_es256(KEY, aud="anon"), "", "https://x/jwks.json")


def test_es256_without_jwks_url_rejected() -> None:
    with pytest.raises(HTTPException):
        auth.decode_token(_es256(KEY), "secret", "")


def test_jwks_url_built_from_project_url() -> None:
    assert auth.jwks_url_for("https://abc.supabase.co/") == (
        "https://abc.supabase.co/auth/v1/.well-known/jwks.json"
    )
    assert auth.jwks_url_for("") == ""
