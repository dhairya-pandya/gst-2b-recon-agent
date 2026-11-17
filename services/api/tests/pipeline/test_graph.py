from datetime import date
from decimal import Decimal

from app.agents.llm import FakeLLM
from app.agents.roles import ResolverOut
from app.guard.budget import Budget
from app.models import BookRow, Gstr2bRow, TaxAmounts
from app.pipeline.graph import Deps, run_pipeline

G1 = "29AAACB1234F1Z5"


def _inputs() -> tuple[list[Gstr2bRow], list[BookRow]]:
    gs = [
        Gstr2bRow(
            supplier_gstin=G1,
            invoice_no="A1",
            invoice_date=date(2026, 11, 5),
            taxable_value=Decimal("1000"),
            tax=TaxAmounts(igst=Decimal("180")),
            period="2026-11",
        ),
        Gstr2bRow(
            supplier_gstin=G1,
            invoice_no="A2",
            invoice_date=date(2026, 11, 6),
            taxable_value=Decimal("1030"),
            tax=TaxAmounts(igst=Decimal("185.4")),
            period="2026-11",
        ),
    ]
    bs = [
        BookRow(
            row_id=1,
            supplier_gstin=G1,
            invoice_no="A1",
            invoice_date=date(2026, 11, 5),
            taxable_value=Decimal("1000"),
            tax=TaxAmounts(igst=Decimal("180")),
        ),
        BookRow(
            row_id=2,
            supplier_gstin=G1,
            invoice_no="A2",
            invoice_date=date(2026, 11, 6),
            taxable_value=Decimal("1000"),
            tax=TaxAmounts(igst=Decimal("180")),
        ),
    ]
    return gs, bs


def _llm() -> FakeLLM:
    return FakeLLM(
        {
            ResolverOut: ResolverOut(
                row_key=f"{G1}|A2",
                likely_cause="amount",
                explanation="Portal taxable 1030 vs books 1000",
                suggested_action="ask supplier",
            )
        }
    )


def test_pipeline_end_to_end_fake_llm() -> None:
    gs, bs = _inputs()
    deps = Deps(llm=_llm(), budget=Budget(10**9, Decimal("1000")), firm_id="firm-1")
    state = run_pipeline("run-1", gs, bs, "2026-11", deps)
    verdicts = [r["verdict"] for r in state["results"]]
    assert verdicts.count("matched") == 1
    assert verdicts.count("partial") == 1
    assert {"match", "resolve", "critic"} <= set(state["timings"])


def test_budget_exhausted_degrades() -> None:
    gs, bs = _inputs()
    deps = Deps(llm=_llm(), budget=Budget(0, Decimal("0")), firm_id="firm-1")
    state = run_pipeline("run-2", gs, bs, "2026-11", deps)
    assert state["degraded"] is True
    assert state["agent_outputs"] == {}
    assert any(r.get("needs_review") for r in state["results"])


def test_resume_from_checkpoint_skips_match() -> None:
    gs, bs = _inputs()
    deps = Deps(llm=_llm(), budget=Budget(10**9, Decimal("1000")), firm_id="firm-1")
    run_pipeline("run-3", gs, bs, "2026-11", deps)
    assert deps.match_calls == 1
    run_pipeline("run-3", gs, bs, "2026-11", deps)  # same thread id: resumes, does not rematch
    assert deps.match_calls == 1
