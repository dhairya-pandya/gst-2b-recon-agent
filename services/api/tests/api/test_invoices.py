import io
from typing import Any

from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas

from tests.api.test_runs import _create_client, _files


def _pdf(lines: list[str]) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    y = 800
    for line in lines:
        c.drawString(72, y, line)
        y -= 20
    c.save()
    return buf.getvalue()


def test_run_accepts_invoice_pdfs(client: TestClient, auth: dict[str, Any]) -> None:
    cid = _create_client(client, auth)
    pdf = _pdf(
        [
            "Tax Invoice",
            "Invoice No: INV/2026/0001",
            "Supplier GSTIN: 27AAPFU0939F1ZV",
            "Total: 1,180.00",
            "Padding text so the page is not treated as a scan by the extractor.",
        ]
    )
    files = [*_files().items(), ("invoices", ("inv1.pdf", pdf, "application/pdf"))]
    r = client.post(
        "/runs", data={"client_id": cid, "period": "2026-11"}, files=files, headers=auth
    )
    assert r.status_code == 201, r.text
    run_id = r.json()["run_id"]
    body = client.get(f"/runs/{run_id}", headers=auth).json()
    assert body["invoices"][0]["invoice_no"] == "INV/2026/0001"
    assert body["invoices"][0]["total"] == "1180.00"
    assert body["invoices"][0]["needs_ocr"] is False


def test_run_without_invoices_still_works(client: TestClient, auth: dict[str, Any]) -> None:
    cid = _create_client(client, auth)
    r = client.post(
        "/runs", data={"client_id": cid, "period": "2026-11"}, files=_files(), headers=auth
    )
    assert r.status_code == 201
    run_id = r.json()["run_id"]
    assert client.get(f"/runs/{run_id}", headers=auth).json()["invoices"] == []


def test_unreadable_invoice_422(client: TestClient, auth: dict[str, Any]) -> None:
    cid = _create_client(client, auth)
    files = [*_files().items(), ("invoices", ("bad.pdf", b"not a pdf", "application/pdf"))]
    r = client.post(
        "/runs", data={"client_id": cid, "period": "2026-11"}, files=files, headers=auth
    )
    assert r.status_code == 422


def test_invoice_total_mismatch_downgrades_matched_row(
    client: TestClient, auth: dict[str, Any]
) -> None:
    cid = _create_client(client, auth)
    pdf = _pdf(
        [
            "Tax Invoice",
            "Invoice No: ABC/101",
            "Supplier GSTIN: 29AAACB1234F1Z5",
            "Total: 1,250.00",
            "Padding text so the page is not treated as a scan by the extractor.",
        ]
    )
    files = [*_files().items(), ("invoices", ("abc101.pdf", pdf, "application/pdf"))]
    r = client.post(
        "/runs", data={"client_id": cid, "period": "2026-11"}, files=files, headers=auth
    )
    assert r.status_code == 201, r.text
    run_id = r.json()["run_id"]
    inv = client.get(f"/runs/{run_id}", headers=auth).json()["invoices"][0]
    assert inv["total_check"] == "total_mismatch"
    rows = client.get(f"/runs/{run_id}/rows", headers=auth).json()
    row = next(x for x in rows if x["book"] and x["book"]["invoice_no"] == "ABC/101")
    assert row["verdict"] == "partial"
    assert "invoice_total_mismatch" in row["reasons"]
