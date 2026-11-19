from datetime import date
from decimal import Decimal

from app.core.invoice_check import check_invoice
from app.ingest.invoices import InvoiceDoc
from app.models import BookRow, TaxAmounts

GSTIN = "27AAPFU0939F1ZV"


def book(row_id: int, inv: str, gst: str = GSTIN) -> BookRow:
    return BookRow(
        row_id=row_id,
        supplier_gstin=gst,
        invoice_no=inv,
        invoice_date=date(2026, 11, 5),
        taxable_value=Decimal("1000"),
        tax=TaxAmounts(cgst=Decimal("90"), sgst=Decimal("90")),
    )


def doc(inv: str | None, total: str | None, gstin: str | None = GSTIN) -> InvoiceDoc:
    return InvoiceDoc(
        filename="x.pdf",
        text="",
        supplier_gstin=gstin,
        invoice_no=inv,
        total=Decimal(total) if total else None,
        needs_ocr=False,
    )


def test_total_within_one_rupee_is_ok() -> None:
    r = check_invoice(doc("INV-1", "1180.50"), [book(7, "INV-1")])
    assert r["book_row_id"] == 7 and r["total_check"] == "ok"


def test_total_beyond_one_rupee_is_mismatch() -> None:
    r = check_invoice(doc("INV-1", "1200"), [book(7, "INV-1")])
    assert r["total_check"] == "total_mismatch" and r["total_gap"] == "20"


def test_invoice_number_canonicalised() -> None:
    r = check_invoice(doc("inv/001", "1180"), [book(3, "INV-001")])
    assert r["book_row_id"] == 3


def test_no_book_row_for_other_supplier() -> None:
    r = check_invoice(doc("INV-1", "1180"), [book(7, "INV-1", gst="29AAPFU0939F1ZV")])
    assert r == {"book_row_id": None, "total_check": "no_unique_book_row"}


def test_missing_invoice_number_not_checked() -> None:
    assert check_invoice(doc(None, "1180"), [book(7, "INV-1")])["total_check"] == "not_checked"


def test_missing_total_reported() -> None:
    r = check_invoice(doc("INV-1", None), [book(7, "INV-1")])
    assert r["total_check"] == "no_total_in_invoice"


def test_apply_checks_downgrades_matched_and_keeps_partial() -> None:
    from app.core.invoice_check import apply_invoice_checks
    from app.core.match import MatchResult, Verdict

    matched = MatchResult(verdict=Verdict.MATCHED, book=book(1, "INV-1"))
    partial = MatchResult(verdict=Verdict.PARTIAL, book=book(2, "INV-2"), reasons=["amount_gap"])
    untouched = MatchResult(verdict=Verdict.MATCHED, book=book(3, "INV-3"))
    checks: list[dict[str, object]] = [
        {"book_row_id": 1, "total_check": "total_mismatch"},
        {"book_row_id": 2, "total_check": "total_mismatch"},
        {"book_row_id": 3, "total_check": "ok"},
    ]
    apply_invoice_checks([matched, partial, untouched], checks)
    assert matched.verdict == Verdict.PARTIAL and matched.reasons == ["invoice_total_mismatch"]
    assert partial.verdict == Verdict.PARTIAL
    assert partial.reasons == ["amount_gap", "invoice_total_mismatch"]
    assert untouched.verdict == Verdict.MATCHED and untouched.reasons == []
