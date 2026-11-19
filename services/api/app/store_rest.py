"""Store backed by Supabase's REST API, called with the signed-in user's own token.

Row-level security applies to every query, so a firm only ever sees its own clients
and runs. No database password is held by the API.
"""

from typing import Any
from uuid import UUID

import httpx
from fastapi import HTTPException


class RestStore:
    def __init__(
        self,
        supabase_url: str,
        anon_key: str,
        token: str,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._client = httpx.Client(
            transport=transport,
            base_url=f"{supabase_url.rstrip('/')}/rest/v1",
            headers={
                "apikey": anon_key,
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=10.0,
        )

    def _check(self, r: httpx.Response) -> Any:
        if r.status_code >= 400:
            raise HTTPException(status_code=502, detail=f"database error ({r.status_code})")
        return r.json() if r.content else None

    def firm_for(self, user_id: str) -> str:
        rows = self._check(
            self._client.get(
                "/memberships", params={"select": "firm_id", "user_id": f"eq.{user_id}", "limit": 1}
            )
        )
        if not rows:
            raise HTTPException(status_code=403, detail="no firm for this account")
        return str(rows[0]["firm_id"])

    def add_client(self, firm: str, name: str, gstin: str) -> dict[str, Any]:
        rows = self._check(
            self._client.post(
                "/clients",
                json={"firm_id": firm, "name": name, "gstin": gstin},
                headers={"Prefer": "return=representation"},
            )
        )
        return {k: rows[0][k] for k in ("id", "firm_id", "name", "gstin")}

    def clients_for(self, firm: str) -> list[dict[str, Any]]:
        return list(
            self._check(
                self._client.get(
                    "/clients",
                    params={
                        "select": "id,firm_id,name,gstin",
                        "firm_id": f"eq.{firm}",
                        "order": "created_at",
                    },
                )
            )
        )

    def client_in(self, firm: str, cid: UUID) -> dict[str, Any] | None:
        rows = self._check(
            self._client.get(
                "/clients",
                params={
                    "select": "id,firm_id,name,gstin",
                    "id": f"eq.{cid}",
                    "firm_id": f"eq.{firm}",
                },
            )
        )
        return rows[0] if rows else None

    def add_run(self, firm: str, client_id: UUID, period: str) -> dict[str, Any]:
        rows = self._check(
            self._client.post(
                "/runs",
                json={"firm_id": firm, "client_id": str(client_id), "period": period},
                headers={"Prefer": "return=representation"},
            )
        )
        r = rows[0]
        return {
            "id": r["id"],
            "firm_id": r["firm_id"],
            "client_id": r["client_id"],
            "period": r["period"],
            "status": r["status"],
        }

    def save_run(self, run: dict[str, Any]) -> None:
        result = {
            k: v
            for k, v in run.items()
            if k not in ("id", "firm_id", "client_id", "period", "status")
        }
        self._check(
            self._client.patch(
                "/runs",
                params={"id": f"eq.{run['id']}"},
                json={"status": run["status"], "result": result},
            )
        )

    def run_in(self, firm: str, rid: UUID) -> dict[str, Any] | None:
        rows = self._check(
            self._client.get(
                "/runs",
                params={
                    "select": "id,firm_id,client_id,period,status,result",
                    "id": f"eq.{rid}",
                    "firm_id": f"eq.{firm}",
                },
            )
        )
        if not rows:
            return None
        r = rows[0]
        return {
            **(r.get("result") or {}),
            "id": r["id"],
            "firm_id": r["firm_id"],
            "client_id": r["client_id"],
            "period": r["period"],
            "status": r["status"],
        }
