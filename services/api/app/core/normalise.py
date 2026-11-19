import re
from functools import lru_cache

_GSTIN_CHARSET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
_GSTIN_RE = re.compile(r"^\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")
_FY_TOKEN_RE = re.compile(r"[/\-](?:20\d{2}|\d{2})-(?:20\d{2}|\d{2})(?=[/\-])")
_SPACE_RE = re.compile(r"\s+")
_SEP_RE = re.compile(r"[/\-_.]")
_PREFIX_DIGITS_RE = re.compile(r"^([A-Z]*)(\d+)$")


def gstin_valid(gstin: str) -> bool:
    """Check GSTIN format and the mod-36 checksum on the last character."""
    gstin = gstin.strip().upper()
    if not _GSTIN_RE.match(gstin):
        return False
    total = 0
    for i, ch in enumerate(gstin[:-1]):
        factor = 1 if i % 2 == 0 else 2
        product = _GSTIN_CHARSET.index(ch) * factor
        total += product // 36 + product % 36
    check = (36 - total % 36) % 36
    return _GSTIN_CHARSET[check] == gstin[-1]


def pan_of(gstin: str) -> str:
    return gstin.strip().upper()[2:12]


@lru_cache(maxsize=1 << 16)
def canon_invoice(no: str) -> str:
    """Uppercase, drop separators and spaces, strip a financial-year token and leading zeros.

    Cached: the same invoice number is canonicalised on both the 2B and book side.
    """
    text = _SPACE_RE.sub("", no.upper())
    text = _FY_TOKEN_RE.sub("", text)
    text = _SEP_RE.sub("", text)
    match = _PREFIX_DIGITS_RE.match(text)
    if match:
        prefix, digits = match.groups()
        return f"{prefix}{int(digits)}"
    return text
