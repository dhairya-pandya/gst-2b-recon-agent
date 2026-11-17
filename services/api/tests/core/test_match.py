import time
from datetime import date
from decimal import Decimal

from app.core.match import Verdict, match
from app.models import BookRow, Gstr2bRow, TaxAmounts

G1 = "29AAACB1234F1Z5"
G2 = "07AABCU9603R1ZX"


def g(gstin: str, no: str, d: int, txval: str, igst: str = "0", cgst: str = "0",
      sgst: str = "0", period: str = "2026-11") -> Gstr2bRow:
    return Gstr2bRow(
        supplier_gstin=gstin, invoice_no=no, invoice_date=date(2026, 11, d),
        taxable_value=Decimal(txval),
        tax=TaxAmounts(igst=Decimal(igst), cgst=Decimal(cgst), sgst=Decimal(sgst)),
        period=period,
    )


def b(row_id: int, gstin: str, no: str, d: int, txval: str, igst: str = "0",
      cgst: str = "0", sgst: str = "0") -> BookRow:
    return BookRow(
        row_id=row_id, supplier_gstin=gstin, invoice_no=no, invoice_date=date(2026, 11, d),
        taxable_value=Decimal(txval),
        tax=TaxAmounts(igst=Decimal(igst), cgst=Decimal(cgst), sgst=Decimal(sgst)),
    )


def verdicts(results: list) -> list[Verdict]:  # type: ignore[type-arg]
    return [r.verdict for r in results]


def test_exact_match() -> None:
    res = match([g(G1, "ABC/101", 5, "1000", igst="180")],
                [b(1, G1, "ABC/101", 5, "1000", igst="180")], "2026-11")
    assert verdicts(res) == [Verdict.MATCHED]


def test_amount_gap_under_1_rupee_matched() -> None:
    res = match([g(G1, "A1", 5, "1000.80", igst="180")],
                [b(1, G1, "A1", 5, "1000", igst="180")], "2026-11")
    assert verdicts(res) == [Verdict.MATCHED]


def test_amount_gap_3pct_partial() -> None:
    res = match([g(G1, "A1", 5, "1030", igst="185.40")],
                [b(1, G1, "A1", 5, "1000", igst="180")], "2026-11")
    assert verdicts(res) == [Verdict.PARTIAL]
    assert "amount_gap" in res[0].reasons


def test_amount_gap_10pct_unmatched() -> None:
    res = match([g(G1, "A1", 5, "1100", igst="198")],
                [b(1, G1, "A1", 5, "1000", igst="180")], "2026-11")
    assert sorted(v.value for v in verdicts(res)) == ["missing_in_2b", "missing_in_books"]


def test_invoice_format_normalised_matched() -> None:
    res = match([g(G1, "ABC/23-24/0101", 5, "1000", igst="180")],
                [b(1, G1, "abc-101", 5, "1000", igst="180")], "2026-11")
    assert verdicts(res) == [Verdict.MATCHED]


def test_missing_both_sides() -> None:
    res = match([g(G1, "X1", 5, "100")], [b(1, G2, "Y9", 5, "100")], "2026-11")
    assert sorted(v.value for v in verdicts(res)) == ["missing_in_2b", "missing_in_books"]


def test_same_pan_diff_gstin_partial() -> None:
    branch = "29AAACB1234F2Z5"  # same PAN (AAACB1234F), different branch code
    res = match([g(G1, "ABC101", 5, "1000", igst="180")],
                [b(1, branch, "ABC101", 5, "1000", igst="180")], "2026-11")
    assert verdicts(res) == [Verdict.PARTIAL]
    assert "gstin_branch" in res[0].reasons


def test_date_outside_window_partial() -> None:
    res = match([g(G1, "A1", 5, "1000", igst="180", period="2026-11")],
                [b(1, G1, "A1", 5, "1000", igst="180")], "2026-08")
    assert verdicts(res) == [Verdict.PARTIAL]
    assert "date_out_of_window" in res[0].reasons


def test_duplicate_book_rows_flagged() -> None:
    res = match([g(G1, "A1", 5, "1000", igst="180")],
                [b(1, G1, "A1", 5, "1000", igst="180"), b(2, G1, "A1", 5, "1000", igst="180")],
                "2026-11")
    assert sorted(v.value for v in verdicts(res)) == ["duplicate", "matched"]


def test_10k_rows_under_2s() -> None:
    gs = [g(G1, f"INV{i}", 5, "100", igst="18") for i in range(10_000)]
    bs = [b(i + 1, G1, f"INV{i}", 5, "100", igst="18") for i in range(10_000)]
    start = time.perf_counter()
    res = match(gs, bs, "2026-11")
    assert time.perf_counter() - start < 2.0
    assert len(res) == 10_000
