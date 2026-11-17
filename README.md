# GST 2B Recon Agent

Multi-agent system that reconciles a client's GSTR-2B against its purchase register and invoice PDFs, flags ITC mismatches, and drafts supplier follow-ups. Built for Indian CA firms.

**Status:** backend core, web design system and benchmark harness built and tested. Database, web sign-in and deploy are not finished — see the status table below.

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
| Ingest (GSTR-2B JSON and Excel, purchase register CSV, invoice PDF) | Built, tested |
| Normalisation and matcher | Built, tested |
| LangGraph pipeline, budgets, checkpoints | Built, tested (fake LLM) |
| Guardrails (scope, PII, rate limit, injection stripping) | Built, tested as logic; not yet wired into all HTTP routes |
| Auth and run endpoints | Built, tested with an in-memory store |
| Supabase schema and row-level security | Written; not yet tested against a live database |
| Legal corpus RAG | Built with a hash embedder; corpus text is paraphrased and awaits verification |
| Web design system and reconciliation row | Built, tested |
| Sign-in (Google / email), full screens | Not built |
| Vertex AI calls and LLM benchmarks | Not run |
| Cloud Run deploy | Dockerfile written; not built or deployed |

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
