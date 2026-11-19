"""In-memory store used until Supabase is reachable. Same shape as the SQL schema."""

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4


@dataclass
class Store:
    clients: dict[UUID, dict[str, Any]] = field(default_factory=dict)
    runs: dict[UUID, dict[str, Any]] = field(default_factory=dict)

    def firm_for(self, user_id: str) -> str:
        return f"firm-{user_id}"  # one owner firm per user at sign-up

    def add_client(self, firm: str, name: str, gstin: str) -> dict[str, Any]:
        cid = uuid4()
        rec = {"id": cid, "firm_id": firm, "name": name, "gstin": gstin}
        self.clients[cid] = rec
        return rec

    def clients_for(self, firm: str) -> list[dict[str, Any]]:
        return [c for c in self.clients.values() if c["firm_id"] == firm]

    def client_in(self, firm: str, cid: UUID) -> dict[str, Any] | None:
        c = self.clients.get(cid)
        return c if c and c["firm_id"] == firm else None

    def add_run(self, firm: str, client_id: UUID, period: str) -> dict[str, Any]:
        rid = uuid4()
        rec: dict[str, Any] = {
            "id": rid,
            "firm_id": firm,
            "client_id": client_id,
            "period": period,
            "status": "queued",
        }
        self.runs[rid] = rec
        return rec

    def save_run(self, run: dict[str, Any]) -> None:
        """Runs are mutated in place in memory; nothing to persist."""

    def run_in(self, firm: str, rid: UUID) -> dict[str, Any] | None:
        r = self.runs.get(rid)
        return r if r and r["firm_id"] == firm else None
