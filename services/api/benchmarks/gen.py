"""Synthetic load generator. Used only for timing and throughput, never for accuracy scoring."""

import json
import random
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

# Planted mismatch mix (share of invoices). Sums to 1.0.
MIX: dict[str, float] = {
    "exact": 0.70,
    "format": 0.10,
    "amount": 0.05,
    "branch": 0.05,
    "missing_2b": 0.05,
    "missing_books": 0.04,
    "duplicate": 0.01,
}
SUPPLIERS = ["29AAACB1234F1Z5", "07AABCU9603R1ZX", "27AAPFU0939F1ZV", "33AABCS1429B1Z2"]
BASE = date(2026, 11, 1)


def _gstin_checksum(body: str) -> str:
    charset = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    total = 0
    for i, ch in enumerate(body):
        factor = 1 if i % 2 == 0 else 2
        product = charset.index(ch) * factor
        total += product // 36 + product % 36
    return charset[(36 - total % 36) % 36]


def generate(out: Path, n_invoices: int, seed: int) -> list[str]:
    """Write gstr2b.json and books.csv for n invoices. Returns the planted kind per invoice."""
    rng = random.Random(seed)
    out.mkdir(parents=True, exist_ok=True)
    kinds: list[str] = []
    for kind, share in MIX.items():
        kinds.extend([kind] * round(n_invoices * share))
    kinds = kinds[:n_invoices]
    while len(kinds) < n_invoices:
        kinds.append("exact")
    rng.shuffle(kinds)

    b2b: dict[str, list[dict[str, object]]] = {}
    books: list[str] = ["supplier_gstin,invoice_no,invoice_date,taxable_value,igst,cgst,sgst,cess"]
    for i, kind in enumerate(kinds):
        gstin = SUPPLIERS[i % len(SUPPLIERS)]
        no = f"INV/{i + 1:06d}"
        day = BASE + timedelta(days=rng.randint(0, 25))
        taxable = Decimal(rng.randint(100, 50_000))
        tax = (taxable * Decimal("0.18")).quantize(Decimal("0.01"))
        book_no, book_gstin, book_tax = no, gstin, tax
        gst_no, gst_tax = no, tax
        if kind == "format":
            book_no = f"inv-{i + 1}"
        elif kind == "amount":
            gst_tax = tax + Decimal("40")
        elif kind == "branch":
            book_gstin = gstin[:-2] + ("Z9" if gstin[-2:] != "Z9" else "Z8")
        elif kind == "missing_2b":
            gst_no = f"NOT-IN-BOOKS-{i}"
        elif kind == "missing_books":
            book_no = f"ONLY-BOOKS-{i}"

        if kind != "missing_books":
            b2b.setdefault(gstin, []).append(
                {
                    "inum": gst_no,
                    "idt": day.strftime("%d-%m-%Y"),
                    "val": float(taxable + gst_tax),
                    "items": [
                        {
                            "itm_det": {
                                "txval": float(taxable),
                                "iamt": float(gst_tax),
                                "camt": 0,
                                "samt": 0,
                                "csamt": 0,
                            }
                        }
                    ],
                }
            )
        if kind != "missing_2b":
            books.append(
                f"{book_gstin},{book_no},{day.strftime('%d-%m-%Y')},{taxable},{book_tax},0,0,0"
            )
            if kind == "duplicate":
                books.append(
                    f"{book_gstin},{book_no},{day.strftime('%d-%m-%Y')},{taxable},{book_tax},0,0,0"
                )

    doc = {
        "data": {
            "gstin": SUPPLIERS[0],
            "rtnprd": "112026",
            "docdata": {"b2b": [{"ctin": g, "inv": inv} for g, inv in b2b.items()]},
        }
    }
    (out / "gstr2b.json").write_text(json.dumps(doc), encoding="utf-8")
    (out / "books.csv").write_text("\n".join(books) + "\n", encoding="utf-8")
    return kinds


MIX_TOTAL = round(sum(MIX.values()), 10)
assert MIX_TOTAL == 1.0
