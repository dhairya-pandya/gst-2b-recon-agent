import json
from typing import Any
from uuid import uuid4

import httpx
import pytest
from fastapi import HTTPException

from app.store_rest import RestStore

FIRM = str(uuid4())


def make(handler: Any) -> tuple[RestStore, list[httpx.Request]]:
    seen: list[httpx.Request] = []

    def wrapped(req: httpx.Request) -> httpx.Response:
        seen.append(req)
        return handler(req)

    store = RestStore("https://p.supabase.co", "anon", "user-token", httpx.MockTransport(wrapped))
    return store, seen


def test_requests_carry_user_token_and_anon_key() -> None:
    store, seen = make(lambda r: httpx.Response(200, json=[{"firm_id": FIRM}]))
    assert store.firm_for("u1") == FIRM
    req = seen[0]
    assert req.headers["Authorization"] == "Bearer user-token"
    assert req.headers["apikey"] == "anon"
    assert req.url.path == "/rest/v1/memberships"


def test_no_membership_is_forbidden() -> None:
    store, _ = make(lambda r: httpx.Response(200, json=[]))
    with pytest.raises(HTTPException) as e:
        store.firm_for("u1")
    assert e.value.status_code == 403


def test_database_error_becomes_502() -> None:
    store, _ = make(lambda r: httpx.Response(401, json={"message": "JWT expired"}))
    with pytest.raises(HTTPException) as e:
        store.clients_for(FIRM)
    assert e.value.status_code == 502


def test_save_and_load_run_round_trip() -> None:
    db: dict[str, Any] = {}
    rid = str(uuid4())

    def handler(r: httpx.Request) -> httpx.Response:
        if r.method == "PATCH":
            db.update(json.loads(r.content))
            return httpx.Response(204)
        row = {"id": rid, "firm_id": FIRM, "client_id": "c", "period": "2026-11", **db}
        return httpx.Response(200, json=[row])

    store, _ = make(handler)
    run = {
        "id": rid,
        "firm_id": FIRM,
        "client_id": "c",
        "period": "2026-11",
        "status": "completed",
        "rows": [{"verdict": "matched"}],
        "counts_by_verdict": {"matched": 1},
    }
    store.save_run(run)
    loaded = store.run_in(FIRM, rid)  # type: ignore[arg-type]
    assert loaded is not None
    assert loaded["status"] == "completed"
    assert loaded["rows"] == [{"verdict": "matched"}]
    assert loaded["counts_by_verdict"] == {"matched": 1}
