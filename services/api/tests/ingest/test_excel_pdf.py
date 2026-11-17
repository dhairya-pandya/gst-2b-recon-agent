import io
from decimal import Decimal

import openpyxl
import pytest
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from app.ingest.gstr2b import parse_gstr2b_excel
from app.ingest.invoices import extract_invoice
from app.models import IngestError


def _xlsx(rows: list[list[object]]) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "B2B"
    ws.append(
        [
            "GSTIN of supplier",
            "Invoice number",
            "Invoice Date",
            "Invoice Value",
            "Taxable Value",
            "Integrated Tax",
            "Central Tax",
            "State/UT Tax",
            "Cess",
        ]
    )
    for r in rows:
        ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_parse_gstr2b_excel_rows() -> None:
    data = _xlsx([["29AAACB1234F1Z5", "ABC/101", "05-11-2026", 1180, 1000, 180, 0, 0, 0]])
    rows = parse_gstr2b_excel(data, period="2026-11")
    assert len(rows) == 1
    assert rows[0].taxable_value == Decimal("1000")
    assert rows[0].tax.igst == Decimal("180")


def test_parse_gstr2b_excel_missing_sheet_raises() -> None:
    wb = openpyxl.Workbook()
    buf = io.BytesIO()
    wb.save(buf)
    with pytest.raises(IngestError) as exc:
        parse_gstr2b_excel(buf.getvalue(), period="2026-11")
    assert exc.value.field == "B2B"


def _pdf(lines: list[str]) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    y = 800
    for line in lines:
        c.drawString(50, y, line)
        y -= 20
    c.save()
    return buf.getvalue()


def test_extract_invoice_fields() -> None:
    data = _pdf(
        [
            "TAX INVOICE",
            "Supplier GSTIN: 29AAACB1234F1Z5",
            "Invoice No: ABC/101",
            "Total: 1180.00",
        ]
    )
    doc = extract_invoice(data, "abc101.pdf")
    assert doc.supplier_gstin == "29AAACB1234F1Z5"
    assert doc.invoice_no == "ABC/101"
    assert doc.total == Decimal("1180.00")
    assert doc.needs_ocr is False


def test_scanned_pdf_flags_needs_ocr() -> None:
    blank = _pdf([])
    doc = extract_invoice(blank, "scan.pdf")
    assert doc.needs_ocr is True
