import time
from typing import Any, Literal
from uuid import UUID

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.config import Settings
from app.core.match import match
from app.guard.auth import CurrentUser
from app.guard.ratelimit import TokenBucket
from app.guard.scope import in_scope
from app.ingest.books import parse_books
from app.ingest.gstr2b import parse_gstr2b_json
from app.ingest.invoices import extract_invoice
from app.models import IngestError
from app.store import Store


class AskIn(BaseModel):
    row_key: str
    question: str = Field(max_length=500)


class ReviewIn(BaseModel):
    row_key: str
    decision: Literal["accept", "reject"]


def _row_key(row: dict[str, Any]) -> str:
    src = row.get("gstr2b") or row.get("book") or {}
    return f"{src.get('supplier_gstin', '')}|{src.get('invoice_no', '')}"


MAX_INVOICES = 200


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
    @app.get("/health")  # /healthz is reserved by Cloud Run's front end; /health is the probe path
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    store: Store = app.state.store
    limiter = TokenBucket(capacity=60, refill_per_sec=1.0)

    @app.middleware("http")
    async def rate_limit(request: Request, call_next: Any) -> Any:
        key = request.headers.get("authorization", "") or (
            request.client.host if request.client else "anon"
        )
        if not limiter.allow(key, time.monotonic()):
            return JSONResponse(
                status_code=429, content={"detail": "rate limited"}, headers={"Retry-After": "1"}
            )
        return await call_next(request)

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
        invoices: list[UploadFile] = File(default=[]),
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
        if len(invoices) > MAX_INVOICES:
            raise HTTPException(status_code=413, detail="too many invoices")
        inv_docs = []
        for f in invoices:
            data = await f.read(settings.max_file_bytes + 1)
            if len(data) > settings.max_file_bytes:
                raise HTTPException(status_code=413, detail="file too large")
            try:
                doc = extract_invoice(data, f.filename or "invoice.pdf")
            except Exception as exc:  # pdfplumber raises several parser error types
                detail = f"unreadable invoice: {f.filename}"
                raise HTTPException(status_code=422, detail=detail) from exc
            inv_docs.append(
                {
                    "filename": doc.filename,
                    "invoice_no": doc.invoice_no,
                    "supplier_gstin": doc.supplier_gstin,
                    "total": str(doc.total) if doc.total is not None else None,
                    "needs_ocr": doc.needs_ocr,
                }
            )

        run = store.add_run(firm, client["id"], period)
        results = match(gs, bs, period)
        counts: dict[str, int] = {}
        for r in results:
            counts[r.verdict.value] = counts.get(r.verdict.value, 0) + 1
        run.update(
            {
                "status": "completed",
                "counts_by_verdict": counts,
                "invoices": inv_docs,
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
            "invoices": run.get("invoices", []),
        }

    @app.post("/runs/{run_id}/ask")
    def ask_row(run_id: str, body: AskIn, user: CurrentUser) -> dict[str, Any]:
        row_key = body.row_key
        run = store.run_in(store.firm_for(user), UUID(run_id))
        if run is None:
            raise HTTPException(status_code=404, detail="run not found")
        if not in_scope(body.question):
            raise HTTPException(status_code=422, detail={"error": "out_of_scope"})
        row = next((r for r in run.get("rows", []) if _row_key(r) == row_key), None)
        if row is None:
            raise HTTPException(status_code=404, detail="row not found")
        return {
            "answer": f"Row {row_key} is {row['verdict']}. Reasons: {row['reasons']}.",
            "grounded_on": row_key,
        }

    @app.post("/runs/{run_id}/reviews", status_code=201)
    def review_row(run_id: str, body: ReviewIn, user: CurrentUser) -> dict[str, str]:
        run = store.run_in(store.firm_for(user), UUID(run_id))
        if run is None:
            raise HTTPException(status_code=404, detail="run not found")
        run.setdefault("reviews", []).append(
            {"row_key": body.row_key, "decision": body.decision, "by": user}
        )
        return {"status": "recorded"}

    @app.get("/runs/{run_id}/rows")
    def get_rows(run_id: str, user: CurrentUser) -> list[dict[str, Any]]:
        run = store.run_in(store.firm_for(user), UUID(run_id))
        if run is None:
            raise HTTPException(status_code=404, detail="run not found")
        return list(run.get("rows", []))

    return app


app = create_app()
