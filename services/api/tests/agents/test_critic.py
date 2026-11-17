from datetime import date
from decimal import Decimal

from app.agents.critic import check_output
from app.core.match import MatchResult, Verdict
from app.models import Gstr2bRow, TaxAmounts


def _row() -> MatchResult:
    return MatchResult(
        verdict=Verdict.PARTIAL,
        gstr2b=Gstr2bRow(
            supplier_gstin="29AAACB1234F1Z5", invoice_no="A1", invoice_date=date(2026, 11, 5),
            taxable_value=Decimal("1000"), tax=TaxAmounts(igst=Decimal("180")), period="2026-11",
        ),
    )


def test_critic_rejects_unknown_citation() -> None:
    problems = check_output(
        reasoning="Eligible under s.99 notice",
        citations=["CGST Act s.99"],
        match=_row(),
        known_citations={"CGST Act s.17(5)(b)"},
    )
    assert any("unknown citation" in p for p in problems)


def test_critic_rejects_invented_amount() -> None:
    problems = check_output(
        reasoning="Tax of 250 is missing",
        citations=[],
        match=_row(),
        known_citations=set(),
    )
    assert any("250" in p for p in problems)


def test_critic_accepts_source_amounts() -> None:
    assert check_output("IGST 180 on 1000", [], _row(), set()) == []
