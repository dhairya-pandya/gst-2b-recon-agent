from decimal import Decimal
from pathlib import Path

import pytest

from app.ingest.gstr2b import parse_gstr2b_json
from app.models import IngestError

FIX = Path(__file__).parent.parent / "fixtures"


def test_parse_gstr2b_json_b2b_rows() -> None:
    rows = parse_gstr2b_json((FIX / "gstr2b_small.json").read_bytes())
    assert len(rows) == 3
    assert rows[0].invoice_no == "ABC/101"
    assert rows[0].taxable_value == Decimal("1000")
    assert rows[0].tax.igst == Decimal("180")
    assert rows[0].period == "2026-11"
    assert rows[2].supplier_gstin == "07AABCU9603R1ZX"


def test_parse_gstr2b_missing_field_raises() -> None:
    data = (FIX / "gstr2b_small.json").read_bytes().replace(b'"inum": "XY-7"', b'"x": "XY-7"')
    with pytest.raises(IngestError) as exc:
        parse_gstr2b_json(data)
    assert exc.value.field == "inum"
