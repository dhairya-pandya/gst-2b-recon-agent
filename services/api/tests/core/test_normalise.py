from app.core.normalise import canon_invoice, gstin_valid, pan_of


def test_gstin_checksum() -> None:
    assert gstin_valid("27AAPFU0939F1ZV") is True
    assert gstin_valid("27AAPFU0939F1ZX") is False


def test_pan_of_gstin() -> None:
    assert pan_of("27AAPFU0939F1ZV") == "AAPFU0939F"


def test_canon_invoice_collapses_formats() -> None:
    assert canon_invoice("ABC/23-24/0101") == canon_invoice("abc-101") == "ABC101"
    assert canon_invoice(" inv 0007 ") == "INV7"
