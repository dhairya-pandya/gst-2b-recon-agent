from typing import Any
from uuid import UUID

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.config import Settings
from app.core.match import match
from app.guard.auth import CurrentUser
from app.ingest.books import parse_books
from app.ingest.gstr2b import parse_gstr2b_json
from app.models import IngestError
from app.store import Store


class ClientIn(BaseModel):
    name: str
    gstin: str


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    app = FastAPI(title="GST 2B Recon API")
    app.state.settings = settings
    app.state.store = Store()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.web_origin],
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @app.exception_handler(IngestError)
    async def _ingest_error(_: Any, exc: IngestError) -> Any:
        from fastapi.responses import JSONResponse

        return JSONResponse(
            status_code=422,
            content={"detail": {"field": exc.field, "row": exc.row, "message": str(exc)}},
        )

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    store: Store = app.state.store

    @app.post("/clients", status_code=201)
    def create_client(body: ClientIn, user: CurrentUser) -> dict[str, Any]:
        firm = store.firm_for(user)
        rec = store.add_client(firm, body.name, body.gstin)
        return {**rec, "id": str(rec["id"])}

    @app.get("/clients")
    def list_clients(user: CurrentUser) -> list[dict[str, Any]]:
        return [{**c, "id": str(c["id"])} for c in store.clients_for(store.firm_for(user))]

    @app.post("/runs", status_code=201)
    async def create_run(
        user: CurrentUser,
        client_id: str = Form(...),
        period: str = Form(...),
        gstr2b: UploadFile = File(...),
        books: UploadFile = File(...),
    ) -> dict[str, Any]:
        firm = store.firm_for(user)
        client = store.client_in(firm, UUID(client_id))
        if client is None:
            raise HTTPException(status_code=404, detail="client not found")
        g_bytes = await gstr2b.read(settings.max_file_bytes + 1)
        b_bytes = await books.read(settings.max_file_bytes + 1)
        if len(g_bytes) > settings.max_file_bytes or len(b_bytes) > settings.max_file_bytes:
            raise HTTPException(status_code=413, detail="file too large")

        gs = parse_gstr2b_json(g_bytes)
        bs = parse_books(b_bytes, books.filename or "books.csv")
        if len(gs) + len(bs) > settings.max_rows:
            raise HTTPException(status_code=413, detail="too many rows")

        run = store.add_run(firm, client["id"], period)
        results = match(gs, bs, period)
        counts: dict[str, int] = {}
        for r in results:
            counts[r.verdict.value] = counts.get(r.verdict.value, 0) + 1
        run.update(
            {
                "status": "completed",
                "counts_by_verdict": counts,
                "rows": [
                    {
                        "verdict": r.verdict.value,
                        "reasons": r.reasons,
                        "gstr2b": r.gstr2b.model_dump(mode="json") if r.gstr2b else None,
                        "book": r.book.model_dump(mode="json") if r.book else None,
                    }
                    for r in results
                ],
            }
        )
        return {"run_id": str(run["id"]), "status": "completed"}

    @app.get("/runs/{run_id}")
    def get_run(run_id: str, user: CurrentUser) -> dict[str, Any]:
        run = store.run_in(store.firm_for(user), UUID(run_id))
        if run is None:
            raise HTTPException(status_code=404, detail="run not found")
        return {
            "id": str(run["id"]),
            "status": run["status"],
            "counts_by_verdict": run.get("counts_by_verdict", {}),
        }

    @app.get("/runs/{run_id}/rows")
    def get_rows(run_id: str, user: CurrentUser) -> list[dict[str, Any]]:
        run = store.run_in(store.firm_for(user), UUID(run_id))
        if run is None:
            raise HTTPException(status_code=404, detail="run not found")
        return list(run.get("rows", []))

    return app
