import csv
import io

from app.ingest.gstr2b import dec, parse_date
from app.models import BookRow, IngestError, TaxAmounts

REQUIRED = [
    "supplier_gstin", "invoice_no", "invoice_date",
    "taxable_value", "igst", "cgst", "sgst", "cess",
]


def parse_books(data: bytes, filename: str) -> list[BookRow]:
    if not filename.lower().endswith(".csv"):
        raise IngestError("file", "only CSV purchase registers are supported")
    reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig")))
    fields = reader.fieldnames or []
    for col in REQUIRED:
        if col not in fields:
            raise IngestError(col, "missing column")

    rows: list[BookRow] = []
    for n, rec in enumerate(reader, start=1):
        rows.append(
            BookRow(
                row_id=n,
                supplier_gstin=rec["supplier_gstin"].strip(),
                invoice_no=rec["invoice_no"].strip(),
                invoice_date=parse_date(rec["invoice_date"].strip(), "invoice_date", n),
                taxable_value=dec(rec["taxable_value"], "taxable_value", n),
                tax=TaxAmounts(
                    igst=dec(rec["igst"] or "0", "igst", n),
                    cgst=dec(rec["cgst"] or "0", "cgst", n),
                    sgst=dec(rec["sgst"] or "0", "sgst", n),
                    cess=dec(rec["cess"] or "0", "cess", n),
                ),
            )
        )
    return rows
