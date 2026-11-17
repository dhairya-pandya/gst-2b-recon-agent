import re
from decimal import Decimal

from app.core.match import MatchResult

_NUM = re.compile(r"\d+(?:\.\d+)?")


def _source_amounts(match: MatchResult) -> set[Decimal]:
    out: set[Decimal] = {Decimal("0")}
    for side in (match.gstr2b, match.book):
        if side is None:
            continue
        out.add(side.taxable_value)
        t = side.tax
        out.update([t.igst, t.cgst, t.sgst, t.cess])
    return out


def check_output(
    reasoning: str,
    citations: list[str],
    match: MatchResult,
    known_citations: set[str],
) -> list[str]:
    """Deterministic checks: every citation must exist, every number must come from source."""
    problems: list[str] = []
    for c in citations:
        if c not in known_citations:
            problems.append(f"unknown citation: {c}")
    allowed = _source_amounts(match)
    for raw in _NUM.findall(reasoning):
        if Decimal(raw) not in allowed:
            problems.append(f"amount not in source: {raw}")
    return problems
