# GST 2B Recon Agent — Architecture Design

Date: 2026-11-17 · Status: approved · Timebox: 4 days

## 1. Intent

Indian CA firms reconcile each client's GSTR-2B against the purchase register by hand in Excel — ICAI use-case pages cite 8–10 hours per client per month. Mismatched GSTINs, invoice-number formats, amount gaps, late supplier filings and blocked credits all need manual chasing.

This project is a production-shaped, multi-agent reconciliation system for those firms. It doubles as a portfolio piece for a Forward Deployed Engineer role: it must visibly demonstrate multi-agent orchestration, RAG over structured + unstructured data, cloud deployment on GCP, guardrails, tracing, and quantified, iteratively optimised pipeline performance.

## 2. Goals, non-goals, anti-goals

**Goals**
- CA logs in (Google or email), uploads a client's GSTR-2B + purchase register + invoice PDFs, gets a reconciled table with verdicts, explanations, ITC eligibility, and supplier follow-up drafts.
- Multi-tenant: firms see only their own clients.
- Measured pipeline performance (stage timings, throughput, cost) improved over documented optimisation rounds.
- Hardened API: rate limits, budgets, scope guardrails, no general-purpose model access.

**Non-goals**
- Filing returns or talking to the GST portal.
- Accuracy evals on synthetic data (explicitly dropped).
- Real client data of any kind.
- Mobile app; Tally integration.

**Anti-goals (failure even if it works)**
- LLM computing or matching amounts.
- Any endpoint usable as a free chatbot / proxy to Gemini.
- Inconsistent UI — screens that don't share the design system.
- Benchmarks without reproducible before/after records.

## 3. Constraints

- 4 days of build.
- Public repo; no mention of AI coding assistants anywhere (code, commits, docs).
- GCP for compute/AI (Cloud Run, Vertex AI Gemini, Cloud Trace, Secret Manager).
- Supabase for auth, Postgres, pgvector, storage. Cloud SQL considered; rejected because it adds separate auth and VPC wiring with no benefit.
- No real data. Generated data used only as benchmark load.

## 4. Approaches considered

| | Approach | Trade-off | Decision |
|---|---|---|---|
| A | Deterministic matching core + agents for judgement, on Google ADK | Accurate, cheap; ADK named in JD | Core split kept |
| B | Fully LLM: model matches both sheets | Fast to build; wrong amounts, costly, untestable | Rejected; kept as benchmark baseline only |
| C | Same split as A, orchestrated with **LangGraph** | Checkpointing, human-in-the-loop interrupts, explicit state | **Chosen** |

## 5. Architecture

```
Next.js (apps/web) ──HTTPS + Supabase JWT──► FastAPI (services/api, Cloud Run)
                                               │
              ┌────────────────────────────────┼──────────────────────────┐
              ▼                                ▼                          ▼
     Guardrail layer                 LangGraph pipeline            Observability
 (auth, rate limit, budget,     parse → normalise → match →     OpenTelemetry → Cloud Trace
  scope check, injection         resolve(agent) → ITC(agent)    + per-step token/cost ledger
  defence, schema validation)    → critic(agent) → draft(agent)
              │                                │
              └──────────────► Supabase: Postgres (RLS by firm_id), pgvector,
                               Storage (PDFs), LangGraph checkpoints, rate/cost tables
                                               │
                                     Vertex AI: Gemini 2.5 Flash / Pro
```

### 5.1 Pipeline (LangGraph graph)

Deterministic nodes (plain Python, no LLM):
1. **Ingest** — parse GSTR-2B JSON/Excel and purchase register into typed rows.
2. **Extract** — invoice PDF text/tables (layout-aware parser; LLM fallback only for unparseable scans).
3. **Normalise** — GSTIN checksum validation, invoice-number canonicalisation, date/amount normalisation.
4. **Match** — exact key match, then blocked fuzzy match (block by GSTIN, rapidfuzz on invoice no., amount tolerance). Outputs Matched / Partial / Missing-in-2B / Missing-in-books.

Agent nodes (Gemini, invoked only on rows needing judgement):
5. **Resolver** (Flash) — explains/proposes resolution for Partial rows.
6. **ITC agent** (Pro) — RAG over CGST Act + circulars in pgvector; eligible/blocked with citation.
7. **Critic** (Pro) — verifies every number against source rows and every citation against the corpus; failure → one retry → human review.
8. **Drafter** (Flash) — supplier follow-up email drafts for Missing-in-2B.
9. **Human review** — LangGraph interrupt; CA approves/rejects suggestions in UI.

Supervisor routes rows; checkpoints persisted to Postgres so runs resume after restarts; tool side effects are idempotent (keyed by run_id + row_id).

### 5.2 Data model (Supabase)

`firms`, `memberships(user_id, firm_id, role)`, `clients`, `runs(client_id, period, status)`, `gstr2b_rows`, `book_rows`, `invoices`, `matches`, `agent_outputs`, `reviews`, `legal_chunks(embedding vector)`, `rate_limits`, `cost_ledger`, `audit_log`. RLS on every tenant table via `firm_id`.

### 5.3 Auth

Supabase Auth: Google OAuth + email magic link. FastAPI verifies the Supabase JWT on every request and resolves firm membership. Service role key only server-side.

### 5.4 Guardrails

1. **No free-form chat endpoint** — only typed task endpoints (upload, reconcile, explain-row, draft-email, review).
2. **Scope check** on any user-typed text (row questions): keyword rules + Flash classifier; off-topic → refusal, logged.
3. **Prompt-injection defence** — PDF text treated as data, delimited, instruction-like spans stripped; agents never get tools beyond their task.
4. **Output validation** — Pydantic schemas; amounts must equal source; citations must exist in corpus.
5. **Rate limits** — token bucket per user and per IP in Postgres (works across Cloud Run instances).
6. **Budgets** — daily token/cost cap per firm; on breach, pipeline degrades to deterministic-only.
7. **Upload limits** — max file size, max rows, allowed MIME types.
8. **PII** — PAN/phone masked in logs and traces.
9. **CORS** locked to the web origin; secrets in Secret Manager.

### 5.5 Frontend

Next.js App Router + TypeScript + Tailwind + shadcn/ui, all driven from one token file.

Screens: sign-in, firm/clients list, new run (upload), reconciliation view, row detail (explanation, ITC citation, critic verdict), review queue, supplier drafts, run trace & cost panel, benchmarks page.

**Design direction — "carbon-copy duplicate book"**: reconciliation view pairs 2B entry (original) with book entry (duplicate); a rubber-stamp verdict mark (Matched / Check / Missing) is the single bold element; everything else quiet.

Tokens: ink `#23306B`, paper `#F7F8F6`, rule `#D9DCD4`, matched `#1E6B47`, check `#A86A12`, missing `#A3261F`. Type: Commissioner, tabular figures for amounts. No mono labels, no all-caps eyebrows. Radius by hierarchy. Accessible contrast, keyboard focus, reduced motion.

### 5.6 Benchmarks and optimisation loop

- **Load generator** — produces realistic GSTR-2B JSON, purchase registers, and invoice PDFs (clean + noisy/scanned-looking) at 1k / 5k / 20k invoices with planted mismatches. Load only; not used to score accuracy.
- **Metrics** — per-stage wall time, end-to-end time per client, invoices/sec, tokens/sec, p50/p95 latency, LLM calls per run, cost per run; baseline B (all-LLM) for comparison.
- **Loop** — baseline → profile → fix top bottleneck → rerun → record. Each round appended to `benchmarks/results/` (commit, change, before, after, delta) and summarised in README.
- **CI** — benchmark smoke run on PRs; fails on regression beyond threshold.

## 6. Engineering standards

- Monorepo: `apps/web`, `services/api`, `benchmarks/`, `docs/`.
- Python: ruff, mypy, pytest. Web: eslint, prettier, vitest.
- Pre-commit hooks; GitHub Actions (lint, test, benchmark smoke); conventional commits; PRs into protected `main`.
- No secrets in repo.

## 7. Scope cuts if behind (in order)

1. Supplier email drafter.
2. 20k-invoice benchmark tier.
3. Design polish beyond core screens.

## 8. Settled calls (author's defaults — open to correction)

- **Inputs** — GSTR-2B: official portal JSON schema and portal Excel export. Purchase register: one documented CSV/Excel template (fixed columns); no arbitrary column-mapping UI.
- **Matching rules** — exact key: supplier GSTIN + canonical invoice no. + financial year. Amount tolerance: ±₹1 per tax head (IGST/CGST/SGST/cess) → Matched; beyond that up to 5% → Partial; else unmatched. Invoice date window: same return period ±1 month. Same PAN, different GSTIN → Partial (branch registration).
- **Pipeline state** — one LangGraph graph per run; rows processed in batches, not one graph per row. Checkpoints per stage, not per row. Run completes with pending review items stored as records; no blocking interrupt per row.
- **Legal corpus** — CGST Act ss. 16–17, CGST Rules 36–37 and 42–43, and the key ITC circulars (e.g. 183/15/2022-GST), sourced from cbic-gst.gov.in. Citation format: `CGST Act s.17(5)(b)`, `Rule 36(4)`, `Circular 183/15/2022`.
- **CI benchmarks** — mocked LLM; measures deterministic stages and orchestration overhead only. LLM-stage benchmarks run manually with real Vertex calls. Baseline B (all-LLM) run at 1k invoices only.
- **Supplier drafts** — draft only; nothing is sent. Visible to members of the owning firm.
- **Sign-up** — open self-serve. First sign-in creates a firm with the user as `owner`; owners invite `member`s. Both roles can run and review; only owners manage members and billing caps. Because anyone can sign up, per-firm budget caps and per-user/IP rate limits are mandatory from day 1, and new firms start on a low daily cap.

## 7a. Definition of done (day 4)

- Deployed Cloud Run API + hosted Next.js web app, publicly reachable.
- One full run end to end: sign up → upload → match → agents → review.
- At least 3 recorded optimisation rounds with before/after numbers.
- Benchmarks page and README table showing them.
- Anything else may be stubbed.

## 9. Left to the builder

Exact PDF parsing library; chunking strategy for legal corpus; rate-limit numbers; budget cap values; benchmark regression threshold; ordering of optimisation rounds (driven by profiling).
