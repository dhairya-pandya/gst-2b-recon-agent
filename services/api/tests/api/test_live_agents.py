from typing import Any

from fastapi.testclient import TestClient

from app.agents.llm import FakeLLM
from app.agents.roles import ResolverOut
from app.config import Settings
from app.main import create_app
from tests.api.conftest import SECRET
from tests.api.test_invoices import _pdf
from tests.api.test_runs import _create_client, _files


def _mismatch_files() -> list[Any]:
    pdf = _pdf(
        [
            "Tax Invoice",
            "Invoice No: ABC/101",
            "Supplier GSTIN: 29AAACB1234F1Z5",
            "Total: 1,250.00",
            "Padding text so the page is not treated as a scan by the extractor.",
        ]
    )
    return [*_files().items(), ("invoices", ("abc101.pdf", pdf, "application/pdf"))]


def _app(llm: Any) -> TestClient:
    settings = Settings(supabase_jwt_secret=SECRET, web_origin="http://localhost:3000")
    return TestClient(create_app(settings, llm=llm))


def _run(c: TestClient, auth: dict[str, Any]) -> str:
    cid = _create_client(c, auth)
    r = c.post(
        "/runs", data={"client_id": cid, "period": "2026-11"}, files=_mismatch_files(), headers=auth
    )
    assert r.status_code == 201, r.text
    return str(r.json()["run_id"])


def test_flagged_row_gets_agent_explanation(auth: dict[str, Any]) -> None:
    fake = FakeLLM(
        {
            ResolverOut: ResolverOut(
                row_key="29AAACB1234F1Z5|ABC/101",
                likely_cause="amount",
                explanation="The PDF total for ABC/101 differs from the books.",
                suggested_action="Ask the supplier for the corrected invoice.",
            )
        }
    )
    c = _app(fake)
    run_id = _run(c, auth)
    assert c.get(f"/runs/{run_id}", headers=auth).json()["agent_status"] == "complete"
    rows = c.get(f"/runs/{run_id}/rows", headers=auth).json()
    flagged = next(x for x in rows if x["verdict"] == "partial")
    assert flagged["agent"]["likely_cause"] == "amount"
    assert flagged["agent"]["problems"] == []  # 101 is an invoice number, not an amount
    matched = next(x for x in rows if x["verdict"] == "matched")
    assert matched["agent"] is None
    assert len(fake.calls) == 1


class _Broken:
    async def structured(self, *a: Any, **k: Any) -> Any:
        raise RuntimeError("quota")


def test_agent_failure_does_not_fail_run(auth: dict[str, Any]) -> None:
    c = _app(_Broken())
    run_id = _run(c, auth)
    assert c.get(f"/runs/{run_id}", headers=auth).json()["agent_status"] == "partial"
    rows = c.get(f"/runs/{run_id}/rows", headers=auth).json()
    assert all(r["agent"] is None for r in rows)


def test_no_key_means_agents_off(client: TestClient, auth: dict[str, Any]) -> None:
    run_id = _run(client, auth)
    assert client.get(f"/runs/{run_id}", headers=auth).json()["agent_status"] == "off"


def test_review_is_returned_with_run(client: TestClient, auth: dict[str, Any]) -> None:
    run_id = _run(client, auth)
    key = "29AAACB1234F1Z5|ABC/101"
    r = client.post(
        f"/runs/{run_id}/reviews", json={"row_key": key, "decision": "accept"}, headers=auth
    )
    assert r.status_code == 201
    reviews = client.get(f"/runs/{run_id}", headers=auth).json()["reviews"]
    assert reviews[-1]["row_key"] == key and reviews[-1]["decision"] == "accept"
