from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class IngestError(ValueError):
    def __init__(self, field: str, message: str, row: int | None = None) -> None:
        super().__init__(f"{field}: {message}" + (f" (row {row})" if row else ""))
        self.field = field
        self.row = row


class TaxAmounts(BaseModel):
    igst: Decimal = Decimal("0")
    cgst: Decimal = Decimal("0")
    sgst: Decimal = Decimal("0")
    cess: Decimal = Decimal("0")


class Gstr2bRow(BaseModel):
    supplier_gstin: str
    invoice_no: str
    invoice_date: date
    taxable_value: Decimal
    tax: TaxAmounts
    period: str  # "YYYY-MM"


class BookRow(BaseModel):
    row_id: int
    supplier_gstin: str
    invoice_no: str
    invoice_date: date
    taxable_value: Decimal
    tax: TaxAmounts
