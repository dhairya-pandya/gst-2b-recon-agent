import time
from typing import Any

import jwt
import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

SECRET = "test-secret-with-at-least-32-bytes-ok!!"


def token(sub: str, firm_hint: str = "") -> str:
    now = int(time.time())
    return jwt.encode(
        {"sub": sub, "aud": "authenticated", "exp": now + 300, "iat": now},
        SECRET,
        algorithm="HS256",
    )


@pytest.fixture
def client() -> TestClient:
    settings = Settings(supabase_jwt_secret=SECRET, web_origin="http://localhost:3000")
    return TestClient(create_app(settings))


@pytest.fixture
def auth() -> dict[str, Any]:
    return {"Authorization": f"Bearer {token('user-a')}"}
