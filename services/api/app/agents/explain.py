"""Live-run agent step: explain flagged rows with Gemini, then check the output.

The deterministic matcher has already decided every verdict. The agent only adds a
plain-language cause and suggested action to rows that need a human. Any failure
(no key, quota, timeout, budget) leaves the row unexplained; the run still completes.
"""

import asyncio
from typing import Any

from app.agents.critic import check_output
from app.agents.llm import LLM
from app.agents.roles import resolve, row_key
from app.core.match import MatchResult, Verdict
from app.guard.budget import Budget

# Free tier allows 5 requests per minute for Flash; stay under it per run.
MAX_EXPLAINED = 5
TOTAL_TIMEOUT_S = 45.0
FLAGGED = {Verdict.PARTIAL, Verdict.MISSING_IN_2B, Verdict.MISSING_IN_BOOKS, Verdict.DUPLICATE}


async def explain_rows(
    llm: LLM | None, results: list[MatchResult], budget: Budget, firm_id: str
) -> tuple[dict[str, dict[str, Any]], str]:
    """Return ({row_key: agent output}, status). Status is one of
    'off', 'none_flagged', 'complete', 'partial'."""
    if llm is None:
        return {}, "off"
    targets = [m for m in results if m.verdict in FLAGGED][:MAX_EXPLAINED]
    if not targets:
        return {}, "none_flagged"
    out: dict[str, dict[str, Any]] = {}

    async def one(m: MatchResult) -> None:
        if not budget.allow(firm_id):
            return
        try:
            res, usage = await resolve(llm, m, "")
        except Exception:  # quota, network, schema: the row stays unexplained
            return
        budget.charge(firm_id, usage)
        # Numbers that are identifiers (invoice number, GSTIN, dates) are not amounts.
        ids = " ".join(
            f"{s.supplier_gstin} {s.invoice_no} {s.invoice_date}" for s in (m.gstr2b, m.book) if s
        )
        problems = [
            p
            for p in check_output(res.explanation, [], m, set())
            if not (p.startswith("amount not in source: ") and p.split(": ", 1)[1] in ids)
        ]
        out[row_key(m)] = {
            "likely_cause": res.likely_cause,
            "explanation": res.explanation,
            "suggested_action": res.suggested_action,
            "problems": problems,
        }

    try:
        await asyncio.wait_for(asyncio.gather(*(one(m) for m in targets)), timeout=TOTAL_TIMEOUT_S)
    except TimeoutError:
        pass
    flagged_total = sum(1 for m in results if m.verdict in FLAGGED)
    status = "complete" if len(out) == flagged_total else "partial"
    return out, status
