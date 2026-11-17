"""Postgres-backed store. Every query runs as the `authenticated` role with the caller's JWT
claims set, so Supabase row-level security enforces firm isolation, not just app code."""

import json
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any
from uuid import UUID

import psycopg


class PgStore:
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    @contextmanager
    def as_user(self, user_id: str) -> Iterator[psycopg.Connection]:
        with psycopg.connect(self._dsn, autocommit=True) as conn:
            conn.execute("set role authenticated")
            conn.execute(
                "select set_config('request.jwt.claims', %s, true)",
                (json.dumps({"sub": user_id, "role": "authenticated"}),),
            )
            yield conn

    def firm_for(self, user_id: str) -> str:
        with self.as_user(user_id) as c:
            row = c.execute("select firm_id from memberships limit 1").fetchone()
        if row is None:
            raise LookupError("no firm membership")
        return str(row[0])

    def add_client(self, user_id: str, name: str, gstin: str) -> dict[str, Any]:
        with self.as_user(user_id) as c:
            row = c.execute(
                "insert into clients (firm_id, name, gstin) "
                "values ((select firm_id from memberships limit 1), %s, %s) "
                "returning id, firm_id, name, gstin",
                (name, gstin),
            ).fetchone()
        assert row is not None
        return {"id": row[0], "firm_id": row[1], "name": row[2], "gstin": row[3]}

    def clients_for(self, user_id: str) -> list[dict[str, Any]]:
        with self.as_user(user_id) as c:
            rows = c.execute("select id, name, gstin from clients order by created_at").fetchall()
        return [{"id": r[0], "name": r[1], "gstin": r[2]} for r in rows]

    def client_exists(self, user_id: str, client_id: UUID) -> bool:
        with self.as_user(user_id) as c:
            row = c.execute("select 1 from clients where id = %s", (client_id,)).fetchone()
        return row is not None

    def run_summary(self, user_id: str, run_id: UUID) -> dict[str, Any] | None:
        with self.as_user(user_id) as c:
            row = c.execute("select id, status from runs where id = %s", (run_id,)).fetchone()
        if row is None:
            return None
        return {"id": str(row[0]), "status": row[1]}
