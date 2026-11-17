from decimal import Decimal

from app.agents.llm import Usage


class Budget:
    """Per-firm daily cap. In-memory here; backed by cost_ledger in the database later."""

    def __init__(self, daily_tokens: int, daily_inr: Decimal) -> None:
        self.daily_tokens = daily_tokens
        self.daily_inr = daily_inr
        self._tokens: dict[str, int] = {}
        self._inr: dict[str, Decimal] = {}

    def allow(self, firm_id: str) -> bool:
        used = self._tokens.get(firm_id, 0)
        spent = self._inr.get(firm_id, Decimal("0"))
        return used < self.daily_tokens and spent < self.daily_inr

    def charge(self, firm_id: str, usage: Usage) -> None:
        tokens = usage.input_tokens + usage.output_tokens
        self._tokens[firm_id] = self._tokens.get(firm_id, 0) + tokens
        self._inr[firm_id] = self._inr.get(firm_id, Decimal("0")) + usage.inr
