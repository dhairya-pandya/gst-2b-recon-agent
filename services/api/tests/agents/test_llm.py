import time
from decimal import Decimal

from pydantic import BaseModel

from app.agents.llm import FakeLLM, Usage, cost_inr, stage


class Verdict(BaseModel):
    ok: bool


def test_fake_llm_returns_schema() -> None:
    llm = FakeLLM({Verdict: Verdict(ok=True)})
    import asyncio

    out, usage = asyncio.run(llm.structured("gemini-2.5-flash", "sys", "user", Verdict))
    assert out == Verdict(ok=True)
    assert isinstance(usage, Usage)


def test_usage_cost_computed() -> None:
    prices = {"m": (Decimal("10"), Decimal("40"))}  # INR per 1M tokens (input, output)
    assert cost_inr("m", 500_000, 250_000, prices=prices) == Decimal("15.000000")


def test_stage_records_timing() -> None:
    timings: dict[str, float] = {}
    with stage("match", timings):
        time.sleep(0.01)
    assert timings["match"] >= 10
