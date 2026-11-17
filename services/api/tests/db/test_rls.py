"""Row-level security tests against a live Supabase Postgres.

Run with: SUPABASE_DB_URL=postgresql://postgres:postgres@127.0.0.1:54322/postgres
    uv run pytest -m db
Skipped automatically when SUPABASE_DB_URL is not set.
"""

import os
import uuid
from collections.abc import Iterator

import psycopg
import pytest

DB_URL = os.environ.get("SUPABASE_DB_URL")
pytestmark = pytest.mark.db


@pytest.fixture
def conn() -> Iterator[psycopg.Connection]:
    if not DB_URL:
        pytest.skip("SUPABASE_DB_URL not set")
    with psycopg.connect(DB_URL, autocommit=True) as c:
        c.execute(
            "truncate table public.firms, public.memberships, public.clients, public.runs cascade"
        )
        c.execute("delete from auth.users")
        yield c


def _user(c: psycopg.Connection, email: str) -> str:
    uid = str(uuid.uuid4())
    c.execute(
        "insert into auth.users (id, email, aud, role) values (%s, %s, 'authenticated', "
        "'authenticated')",
        (uid, email),
    )
    return uid


def _as(c: psycopg.Connection, uid: str) -> None:
    c.execute("set role authenticated")
    c.execute(
        "select set_config('request.jwt.claims', %s, false)",
        (f'{{"sub": "{uid}", "role": "authenticated"}}',),
    )


def _reset(c: psycopg.Connection) -> None:
    c.execute("reset role")


def test_signup_creates_firm_owner(conn: psycopg.Connection) -> None:
    uid = _user(conn, "owner@firm.test")
    _reset(conn)
    row = conn.execute("select role from public.memberships where user_id = %s", (uid,)).fetchone()
    assert row == ("owner",)


def test_user_cannot_read_other_firm_runs(conn: psycopg.Connection) -> None:
    a = _user(conn, "a@firm.test")
    b = _user(conn, "b@firm.test")
    _reset(conn)
    firm_a = conn.execute(
        "select firm_id from public.memberships where user_id = %s", (a,)
    ).fetchone()[0]
    client_a = conn.execute(
        "insert into public.clients (firm_id, name, gstin) values (%s, 'Acme', "
        "'27AAPFU0939F1ZV') returning id",
        (firm_a,),
    ).fetchone()[0]
    conn.execute(
        "insert into public.runs (firm_id, client_id, period) values (%s, %s, '2026-11')",
        (firm_a, client_a),
    )

    _as(conn, a)
    own = conn.execute("select count(*) from public.runs").fetchone()[0]
    _as(conn, b)
    other = conn.execute("select count(*) from public.runs").fetchone()[0]
    _reset(conn)
    assert own == 1
    assert other == 0


def test_user_cannot_insert_into_other_firm(conn: psycopg.Connection) -> None:
    a = _user(conn, "c@firm.test")
    b = _user(conn, "d@firm.test")
    _reset(conn)
    firm_a = conn.execute(
        "select firm_id from public.memberships where user_id = %s", (a,)
    ).fetchone()[0]
    _as(conn, b)
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        conn.execute(
            "insert into public.clients (firm_id, name, gstin) values (%s, 'X', '27AAPFU0939F1ZV')",
            (firm_a,),
        )
    _reset(conn)
