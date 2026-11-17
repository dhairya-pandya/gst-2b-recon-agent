from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from tests.api.conftest import token

FIX = Path(__file__).parent.parent / "fixtures"


def _files(gstr2b: bytes | None = None) -> dict[str, Any]:
    return {
        "gstr2b": (
            "gstr2b.json",
            gstr2b or (FIX / "gstr2b_small.json").read_bytes(),
            "application/json",
        ),
        "books": ("books.csv", (FIX / "books_small.csv").read_bytes(), "text/csv"),
    }


def _create_client(c: TestClient, h: dict[str, str]) -> str:
    r = c.post("/clients", json={"name": "Acme", "gstin": "27AAPFU0939F1ZV"}, headers=h)
    assert r.status_code == 201
    return str(r.json()["id"])


def test_missing_token_401(client: TestClient) -> None:
    r = client.get("/clients")
    assert r.status_code == 401


def test_bad_gstr2b_returns_422_with_field(client: TestClient, auth: dict[str, str]) -> None:
    cid = _create_client(client, auth)
    bad = (FIX / "gstr2b_small.json").read_bytes().replace(b'"inum"', b'"x"')
    r = client.post(
        "/runs", data={"client_id": cid, "period": "2026-11"}, files=_files(bad), headers=auth
    )
    assert r.status_code == 422
    assert r.json()["detail"]["field"] == "inum"


def test_oversize_file_413(client: TestClient, auth: dict[str, str]) -> None:
    cid = _create_client(client, auth)
    big = b"{" + b" " * (10 * 1024 * 1024 + 1) + b"}"
    r = client.post(
        "/runs", data={"client_id": cid, "period": "2026-11"}, files=_files(big), headers=auth
    )
    assert r.status_code == 413


def test_other_firm_run_404(client: TestClient, auth: dict[str, str]) -> None:
    cid = _create_client(client, auth)
    r = client.post(
        "/runs", data={"client_id": cid, "period": "2026-11"}, files=_files(), headers=auth
    )
    run_id = r.json()["run_id"]
    other = {"Authorization": f"Bearer {token('user-b')}"}
    assert client.get(f"/runs/{run_id}", headers=other).status_code == 404
    assert client.get(f"/runs/{run_id}", headers=auth).status_code == 200


def test_create_run_completes_with_counts(client: TestClient, auth: dict[str, str]) -> None:
    cid = _create_client(client, auth)
    r = client.post(
        "/runs", data={"client_id": cid, "period": "2026-11"}, files=_files(), headers=auth
    )
    assert r.status_code == 201
    body = client.get(f"/runs/{r.json()['run_id']}", headers=auth).json()
    assert body["status"] == "completed"
    assert sum(body["counts_by_verdict"].values()) == 3
