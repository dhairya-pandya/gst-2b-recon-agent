import io
import re
from decimal import Decimal, InvalidOperation

import pdfplumber
from pydantic import BaseModel

_GSTIN = re.compile(r"\b\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]\b")
_INV_NO = re.compile(r"Invoice\s*(?:No\.?|Number|#)\s*[:\-]?\s*([A-Za-z0-9/\-_.]+)", re.IGNORECASE)
_TOTAL = re.compile(r"Total\s*[:\-]?\s*([\d,]+(?:\.\d+)?)", re.IGNORECASE)
OCR_THRESHOLD = 50


class InvoiceDoc(BaseModel):
    filename: str
    text: str
    supplier_gstin: str | None
    invoice_no: str | None
    total: Decimal | None
    needs_ocr: bool


def extract_invoice(data: bytes, filename: str) -> InvoiceDoc:
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        text = "\n".join((page.extract_text() or "") for page in pdf.pages)
    gstin = _GSTIN.search(text)
    inv = _INV_NO.search(text)
    total_match = _TOTAL.search(text)
    total: Decimal | None = None
    if total_match:
        try:
            total = Decimal(total_match.group(1).replace(",", ""))
        except InvalidOperation:
            total = None
    return InvoiceDoc(
        filename=filename,
        text=text,
        supplier_gstin=gstin.group(0) if gstin else None,
        invoice_no=inv.group(1) if inv else None,
        total=total,
        needs_ocr=len(text.strip()) < OCR_THRESHOLD,
    )
