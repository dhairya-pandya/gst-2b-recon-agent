import re

_GSTIN_CHARSET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
_GSTIN_RE = re.compile(r"^\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")
_FY_TOKEN_RE = re.compile(r"[/\-](?:20\d{2}|\d{2})-(?:20\d{2}|\d{2})(?=[/\-])")


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


def canon_invoice(no: str) -> str:
    """Uppercase, drop separators and spaces, strip a financial-year token and leading zeros."""
    text = re.sub(r"\s+", "", no.upper())
    text = _FY_TOKEN_RE.sub("", text)
    text = re.sub(r"[/\-_.]", "", text)
    match = re.match(r"^([A-Z]*)(\d+)$", text)
    if match:
        prefix, digits = match.groups()
        return f"{prefix}{int(digits)}"
    return text
