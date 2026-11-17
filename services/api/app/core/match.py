from datetime import date
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel
from rapidfuzz import fuzz

from app.core.normalise import canon_invoice, pan_of
from app.models import BookRow, Gstr2bRow, TaxAmounts

ABS_TOLERANCE = Decimal("1")  # per tax head, rupees
PARTIAL_MAX_PCT = Decimal("0.05")
FUZZY_MIN = 90


class Verdict(StrEnum):
    MATCHED = "matched"
    PARTIAL = "partial"
    MISSING_IN_2B = "missing_in_2b"
    MISSING_IN_BOOKS = "missing_in_books"
    DUPLICATE = "duplicate"


class MatchResult(BaseModel):
    verdict: Verdict
    gstr2b: Gstr2bRow | None = None
    book: BookRow | None = None
    reasons: list[str] = []
    amount_gap: TaxAmounts | None = None


def _heads(t: TaxAmounts) -> list[Decimal]:
    return [t.igst, t.cgst, t.sgst, t.cess]


def _total(r_txval: Decimal, t: TaxAmounts) -> Decimal:
    return r_txval + sum(_heads(t), Decimal(0))


def _gap(a: Gstr2bRow, b: BookRow) -> tuple[TaxAmounts, bool, bool]:
    """Return per-head gap (2B minus books), whether all heads within tolerance,
    and whether total gap is within the partial band."""
    gap = TaxAmounts(
        igst=a.tax.igst - b.tax.igst,
        cgst=a.tax.cgst - b.tax.cgst,
        sgst=a.tax.sgst - b.tax.sgst,
        cess=a.tax.cess - b.tax.cess,
    )
    within_head = all(abs(x) <= ABS_TOLERANCE for x in _heads(gap))
    book_total = _total(b.taxable_value, b.tax)
    total_gap = abs(_total(a.taxable_value, a.tax) - book_total)
    within_partial = book_total > 0 and total_gap / book_total <= PARTIAL_MAX_PCT
    return gap, within_head, within_partial


def _window_ok(a: Gstr2bRow, book_date: date, period: str) -> bool:
    py, pm = (int(x) for x in period.split("-"))
    months_gap = abs((py * 12 + pm) - (book_date.year * 12 + book_date.month))
    return months_gap <= 1


def _key(gstin: str, invoice_no: str) -> tuple[str, str]:
    return gstin.strip().upper(), canon_invoice(invoice_no)


def match(gstr2b: list[Gstr2bRow], books: list[BookRow], period: str) -> list[MatchResult]:
    results: list[MatchResult] = []

    # Duplicates: second and later book rows sharing a (gstin, canonical invoice) key.
    seen: dict[tuple[str, str], BookRow] = {}
    unique_books: list[BookRow] = []
    for book in books:
        k = _key(book.supplier_gstin, book.invoice_no)
        if k in seen:
            results.append(MatchResult(verdict=Verdict.DUPLICATE, book=book,
                                       reasons=["duplicate_in_books"]))
        else:
            seen[k] = book
            unique_books.append(book)

    # Pass 1: exact key.
    book_by_key = {_key(b.supplier_gstin, b.invoice_no): b for b in unique_books}
    used_books: set[int] = set()
    leftover_2b: list[Gstr2bRow] = []
    for row in gstr2b:
        b = book_by_key.get(_key(row.supplier_gstin, row.invoice_no))
        if b is None or b.row_id in used_books:
            leftover_2b.append(row)
            continue
        paired = _pair(row, b, period)
        if paired is None:
            leftover_2b.append(row)
            continue
        used_books.add(b.row_id)
        results.append(paired)

    # Pass 2: same PAN, fuzzy invoice number, taxable value within tolerance → branch partial.
    remaining_books = [b for b in unique_books if b.row_id not in used_books]
    still_2b: list[Gstr2bRow] = []
    for row in leftover_2b:
        candidate = None
        for b in remaining_books:
            if pan_of(b.supplier_gstin) != pan_of(row.supplier_gstin):
                continue
            score = fuzz.ratio(canon_invoice(row.invoice_no), canon_invoice(b.invoice_no))
            if score >= FUZZY_MIN and abs(b.taxable_value - row.taxable_value) <= ABS_TOLERANCE:
                candidate = b
                break
        if candidate is None:
            still_2b.append(row)
            continue
        remaining_books.remove(candidate)
        used_books.add(candidate.row_id)
        reasons = ["gstin_branch"]
        if row.supplier_gstin.strip().upper() == candidate.supplier_gstin.strip().upper():
            reasons = []
        results.append(MatchResult(verdict=Verdict.PARTIAL, gstr2b=row, book=candidate,
                                   reasons=reasons))

    for row in still_2b:
        results.append(MatchResult(verdict=Verdict.MISSING_IN_BOOKS, gstr2b=row))
    for b in unique_books:
        if b.row_id not in used_books:
            results.append(MatchResult(verdict=Verdict.MISSING_IN_2B, book=b))
    return results


def _pair(row: Gstr2bRow, b: BookRow, period: str) -> MatchResult | None:
    gap, within_head, within_partial = _gap(row, b)
    if not within_head and not within_partial:
        return None  # too far apart to be the same invoice
    reasons: list[str] = []
    if not _window_ok(row, b.invoice_date, period):
        reasons.append("date_out_of_window")
    if not within_head:
        reasons.append("amount_gap")
    verdict = Verdict.MATCHED if within_head and not reasons else Verdict.PARTIAL
    return MatchResult(verdict=verdict, gstr2b=row, book=b, reasons=reasons, amount_gap=gap)

