import json
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from app.models import Gstr2bRow, IngestError, TaxAmounts


def dec(value: Any, field: str, row: int | None = None) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError) as exc:
        raise IngestError(field, f"not a number: {value!r}", row) from exc


def parse_date(value: Any, field: str, row: int | None = None) -> date:
    try:
        return datetime.strptime(str(value), "%d-%m-%Y").date()
    except ValueError as exc:
        raise IngestError(field, f"expected DD-MM-YYYY: {value!r}", row) from exc


def require(obj: dict[str, Any], key: str, row: int | None = None) -> Any:
    if key not in obj:
        raise IngestError(key, "missing field", row)
    return obj[key]


def parse_gstr2b_json(data: bytes) -> list[Gstr2bRow]:
    try:
        doc = json.loads(data)
    except json.JSONDecodeError as exc:
        raise IngestError("json", str(exc)) from exc

    data_node = require(doc, "data")
    docdata = require(data_node, "docdata")
    period_raw = str(require(data_node, "rtnprd"))
    period = f"{period_raw[2:6]}-{period_raw[:2]}"

    rows: list[Gstr2bRow] = []
    counter = 0
    for supplier in require(docdata, "b2b"):
        gstin = str(require(supplier, "ctin"))
        for inv in require(supplier, "inv"):
            counter += 1
            det = require(require(inv, "items")[0], "itm_det")
            rows.append(
                Gstr2bRow(
                    supplier_gstin=gstin,
                    invoice_no=str(require(inv, "inum", counter)),
                    invoice_date=parse_date(require(inv, "idt", counter), "idt", counter),
                    taxable_value=dec(require(det, "txval", counter), "txval", counter),
                    tax=TaxAmounts(
                        igst=dec(det.get("iamt", 0), "iamt", counter),
                        cgst=dec(det.get("camt", 0), "camt", counter),
                        sgst=dec(det.get("samt", 0), "samt", counter),
                        cess=dec(det.get("csamt", 0), "csamt", counter),
                    ),
                    period=period,
                )
            )
    return rows


def parse_gstr2b_excel(data: bytes) -> list[Gstr2bRow]:
    raise NotImplementedError("Excel export parser: added after JSON path is green")
