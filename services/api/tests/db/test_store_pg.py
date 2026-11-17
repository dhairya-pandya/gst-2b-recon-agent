import os
import uuid

import psycopg
import pytest

from app.store_pg import PgStore

DB_URL = os.environ.get("SUPABASE_DB_URL")
pytestmark = pytest.mark.db


@pytest.fixture
def store() -> PgStore:
    if not DB_URL:
        pytest.skip("SUPABASE_DB_URL not set")
    with psycopg.connect(DB_URL, autocommit=True) as c:
        c.execute("delete from auth.users")
    return PgStore(DB_URL)


def _signup(email: str) -> str:
    uid = str(uuid.uuid4())
    with psycopg.connect(DB_URL, autocommit=True) as c:  # type: ignore[arg-type]
        c.execute(
            "insert into auth.users (id, email, aud, role) values (%s, %s, "
            "'authenticated', 'authenticated')",
            (uid, email),
        )
    return uid


def test_client_round_trip_is_firm_scoped(store: PgStore) -> None:
    a = _signup("pg-a@firm.test")
    b = _signup("pg-b@firm.test")
    rec = store.add_client(a, "Acme", "27AAPFU0939F1ZV")
    assert store.clients_for(a)[0]["name"] == "Acme"
    assert store.clients_for(b) == []
    assert store.client_exists(b, rec["id"]) is False
