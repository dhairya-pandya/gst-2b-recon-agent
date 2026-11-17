from decimal import Decimal
from pathlib import Path

import pytest

from app.ingest.books import parse_books
from app.models import IngestError

FIX = Path(__file__).parent.parent / "fixtures"


def test_parse_books_csv() -> None:
    rows = parse_books((FIX / "books_small.csv").read_bytes(), "books_small.csv")
    assert [r.row_id for r in rows] == [1, 2, 3]
    assert rows[1].tax.cgst == Decimal("180.00")


def test_parse_books_bad_date_raises() -> None:
    bad = (
        b"supplier_gstin,invoice_no,invoice_date,taxable_value,igst,cgst,sgst,cess\n"
        b"29AAACB1234F1Z5,A1,05-11-2026,1,0,0,0,0\n"
        b"29AAACB1234F1Z5,A2,2026/11/05,1,0,0,0,0\n"
    )
    with pytest.raises(IngestError) as exc:
        parse_books(bad, "bad.csv")
    assert exc.value.field == "invoice_date"
    assert exc.value.row == 2
