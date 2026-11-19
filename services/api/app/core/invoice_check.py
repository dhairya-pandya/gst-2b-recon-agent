from decimal import Decimal
from typing import Any

from app.core.normalise import canon_invoice
from app.ingest.invoices import InvoiceDoc
from app.models import BookRow

TOTAL_TOLERANCE = Decimal("1")


def book_gross(row: BookRow) -> Decimal:
    t = row.tax
    return row.taxable_value + t.igst + t.cgst + t.sgst + t.cess


def check_invoice(doc: InvoiceDoc, books: list[BookRow]) -> dict[str, object]:
    """Link an invoice PDF to a book row and compare its total with the row's gross value.

    Deterministic only. Verdicts are not changed; the result is shown beside the run.
    """
    if not doc.invoice_no or not doc.supplier_gstin:
        return {"book_row_id": None, "total_check": "not_checked"}
    key = canon_invoice(doc.invoice_no)
    hits = [
        b
        for b in books
        if b.supplier_gstin == doc.supplier_gstin and canon_invoice(b.invoice_no) == key
    ]
    if len(hits) != 1:
        return {"book_row_id": None, "total_check": "no_unique_book_row"}
    row = hits[0]
    if doc.total is None:
        return {"book_row_id": row.row_id, "total_check": "no_total_in_invoice"}
    gap = abs(doc.total - book_gross(row))
    return {
        "book_row_id": row.row_id,
        "total_check": "ok" if gap <= TOTAL_TOLERANCE else "total_mismatch",
        "total_gap": str(gap),
    }


def apply_invoice_checks(results: list[Any], checks: list[dict[str, object]]) -> list[Any]:
    """Downgrade rows whose invoice PDF total disagrees with the book.

    A Matched row becomes Partial with reason ``invoice_total_mismatch``; rows that already
    need review keep their verdict and gain the reason. Returns the same list.
    """
    from app.core.match import Verdict

    bad = {c["book_row_id"] for c in checks if c.get("total_check") == "total_mismatch"}
    for r in results:
        if r.book is None or r.book.row_id not in bad:
            continue
        if "invoice_total_mismatch" not in r.reasons:
            r.reasons = [*r.reasons, "invoice_total_mismatch"]
        if r.verdict == Verdict.MATCHED:
            r.verdict = Verdict.PARTIAL
    return results
