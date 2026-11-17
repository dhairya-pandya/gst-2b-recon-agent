import re

_PAN = re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b")
_PHONE = re.compile(r"\b[6-9]\d{9}\b")


def mask_pii(text: str) -> str:
    text = _PAN.sub("XXXXX####X", text)
    return _PHONE.sub("**********", text)
