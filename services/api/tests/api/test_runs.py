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


def test_run_rows_returned_with_verdicts(client: TestClient, auth: dict[str, str]) -> None:
    cid = _create_client(client, auth)
    r = client.post(
        "/runs", data={"client_id": cid, "period": "2026-11"}, files=_files(), headers=auth
    )
    run_id = r.json()["run_id"]
    body = client.get(f"/runs/{run_id}/rows", headers=auth).json()
    assert len(body) == 3
    assert {row["verdict"] for row in body} <= {
        "matched",
        "partial",
        "missing_in_2b",
        "missing_in_books",
        "duplicate",
    }
    first = body[0]
    assert "invoice_no" in first["gstr2b"] or "invoice_no" in first["book"]


def test_run_rows_other_firm_404(client: TestClient, auth: dict[str, str]) -> None:
    cid = _create_client(client, auth)
    run_id = client.post(
        "/runs", data={"client_id": cid, "period": "2026-11"}, files=_files(), headers=auth
    ).json()["run_id"]
    other = {"Authorization": f"Bearer {token('user-b')}"}
    assert client.get(f"/runs/{run_id}/rows", headers=other).status_code == 404


def _run_with_rows(client: TestClient, auth: dict[str, str]) -> tuple[str, str]:
    cid = _create_client(client, auth)
    run_id = client.post(
        "/runs", data={"client_id": cid, "period": "2026-11"}, files=_files(), headers=auth
    ).json()["run_id"]
    key = client.get(f"/runs/{run_id}/rows", headers=auth).json()[0]["gstr2b"]
    return run_id, f"{key['supplier_gstin']}|{key['invoice_no']}"


def test_ask_off_topic_refused(client: TestClient, auth: dict[str, str]) -> None:
    run_id, key = _run_with_rows(client, auth)
    r = client.post(
        f"/runs/{run_id}/ask",
        json={"row_key": key, "question": "write me a poem about cats"},
        headers=auth,
    )
    assert r.status_code == 422
    assert r.json()["detail"]["error"] == "out_of_scope"


def test_ask_on_topic_answered(client: TestClient, auth: dict[str, str]) -> None:
    run_id, key = _run_with_rows(client, auth)
    r = client.post(
        f"/runs/{run_id}/ask",
        json={"row_key": key, "question": "Why is this invoice partial in my GST 2B?"},
        headers=auth,
    )
    assert r.status_code == 200
    assert "answer" in r.json()


def test_review_accept_recorded(client: TestClient, auth: dict[str, str]) -> None:
    run_id, key = _run_with_rows(client, auth)
    r = client.post(
        f"/runs/{run_id}/reviews", json={"row_key": key, "decision": "accept"}, headers=auth
    )
    assert r.status_code == 201


def test_rate_limit_429_after_burst(client: TestClient, auth: dict[str, str]) -> None:
    codes = [client.get("/clients", headers=auth).status_code for _ in range(65)]
    assert codes[-1] == 429
    assert codes.count(200) == 60
