# GST 2B Recon Agent

Multi-agent system that reconciles a client's GSTR-2B against its purchase register and invoice PDFs, flags ITC mismatches, and drafts supplier follow-ups. Built for Indian CA firms.

**Status:** backend, database security (row-level security verified locally), web app and benchmark harness built and tested. The API and web app are deployed to Cloud Run. Google sign-in and live Vertex AI calls are not yet verified — see the status table below.

## Problem

CA firms reconcile GSTR-2B against their books by hand in Excel. ICAI's own use-case pages put this at 8–10 hours per client per month.

## How it works

- **Plain code does the matching.** GSTIN checksums, invoice-number normalisation, ₹1 per-tax-head tolerance, 5% partial band, branch detection and duplicate detection. Deterministic, testable, cheap.
- **Gemini agents handle only judgement:** resolving partial rows, ITC eligibility against cited CGST provisions, a critic that checks every cited citation and number against the source, and supplier reminder drafts.
- **LangGraph** orchestrates the pipeline with checkpoints, so a crashed run resumes without re-matching.
- **Guardrails:** typed endpoints only (no free-form chat), scope gate, prompt-injection stripping on document text, PII masking, token-bucket rate limits, per-firm budgets with a deterministic fallback.

## Performance

Synthetic load only, fake LLM (no Vertex calls yet). Accuracy is not scored on synthetic data. Full log: [`services/api/benchmarks/results/LOG.md`](services/api/benchmarks/results/LOG.md).

| Round | Change | Size | Stage | Before | After |
|---|---|---|---|---|---|
| 1 | Index books by PAN; compute keys once | 20k invoices | match | 1,522 ms | 222 ms |
| 1 | same | 20k invoices | end-to-end pipeline | 1,912 ms | 613 ms |
| 2 | Keep pipeline inputs out of checkpointed state | 20k invoices | end-to-end pipeline | 613 ms | 425 ms |

Reproduce: `cd services/api && uv run python -m benchmarks.run --size 20000`

## Status

| Area | State |
|---|---|
| Ingest (GSTR-2B JSON and Excel, purchase register CSV, invoice PDF) | Built, tested; invoice PDFs are parsed and their totals checked against matching book rows (reported, verdicts unchanged) |
| Normalisation and matcher | Built, tested |
| LangGraph pipeline, budgets, checkpoints | Built, tested (fake LLM) |
| Guardrails (scope, PII, rate limit, injection stripping) | Built, tested as logic; not yet wired into all HTTP routes |
| Auth, run, row-question and review endpoints | Built, tested; run data still in memory (not yet on Postgres) |
| Supabase schema and row-level security | Built and verified against a local Supabase: 4 RLS tests pass (cross-firm reads and writes blocked) |
| Legal corpus RAG | Built with a hash embedder; corpus text is paraphrased and awaits verification |
| Web design system, sign-in page, clients page, new-run page, reconciliation table | Built, tested (21 web tests); sign-in page renders in the deployed app |
| Google and email sign-in end to end | Email and Google flows are coded; not yet exercised end to end. Google OAuth client not configured |
| Vertex AI calls and LLM benchmarks | Client written and unit-tested with a mock; no live calls run yet (needs GCP project) |
| Cloud Run deploy | API and web app deployed to Cloud Run (asia-south1). Auth rejects requests without a token; CORS allows the web origin |

## Layout

```
services/api/   FastAPI, pipeline, guardrails, benchmarks
apps/web/       Next.js app and design system
corpus/         Legal corpus (paraphrased; see SOURCES.md)
supabase/       Schema and row-level security
docs/           Design and implementation plan
```

## Development

- API: `cd services/api && uv sync && uv run pytest && uv run ruff check . && uv run mypy app`
- Web: `cd apps/web && pnpm install && pnpm test && pnpm build`
