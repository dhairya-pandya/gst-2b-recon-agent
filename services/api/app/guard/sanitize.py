import re

_INJECTION = re.compile(
    r"(ignore\s+(all\s+)?(previous|prior|above)|system\s*:|you\s+are\s+now|<\|.*?\|>|"
    r"disregard\s+(the\s+)?(rules|instructions))",
    re.IGNORECASE,
)


def wrap_untrusted(text: str) -> str:
    """Treat document text as data: drop instruction-like lines, then delimit."""
    kept = [line for line in text.splitlines() if not _INJECTION.search(line)]
    body = "\n".join(kept)
    return f"<untrusted_document>\n{body}\n</untrusted_document>"
