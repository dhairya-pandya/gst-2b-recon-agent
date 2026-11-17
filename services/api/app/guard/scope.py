import re

# Checked first: general-purpose requests are refused even if they mention GST.
_BLOCK = re.compile(
    r"\b(poem|story|joke|translate|recipe|song|essay|code for|write me|ignore|"
    r"weather|horoscope|stock tip)\b",
    re.IGNORECASE,
)
_ALLOW = re.compile(
    r"\b(gst|gstin|gstr|itc|invoice|2b|supplier|credit|tax|reconcil\w*|"
    r"purchase register|cgst|sgst|igst|cess)\b",
    re.IGNORECASE,
)


def in_scope(text: str) -> bool:
    """Deterministic scope gate. Default deny; a classifier can second-opinion later."""
    if _BLOCK.search(text):
        return False
    return bool(_ALLOW.search(text))
