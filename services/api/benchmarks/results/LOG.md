# Benchmark log

Speed only. Synthetic load, fake LLM (no Vertex calls yet). Accuracy is not scored here.
Measured on the author's laptop (Apple Silicon, Python 3.12). Times in milliseconds.

| Round | Commit | Change | Size | Stage | Before | After | Delta |
|---|---|---|---|---|---|---|---|
| 0 | 0987936 | baseline | 5k | match | 114.8 | — | — |
| 0 | 0987936 | baseline | 20k | match | 1522.1 | — | — |
| 0 | 0987936 | baseline | 20k | pipeline end-to-end | 1912.4 | — | — |
| 1 | cf53d0c | Index books by PAN; compute canonical keys once per row (was recomputed per pair; profile showed 917k `canon_invoice` and 3.8M `pan_of` calls at 20k) | 5k | match | 114.8 | 32.6 | −72% |
| 1 | cf53d0c | same | 20k | match | 1522.1 | 222.4 | −85% |
| 1 | cf53d0c | same | 20k | pipeline end-to-end | 1912.4 | 612.6 | −68% |

Verdict counts at 20k are consistent with the planted mix (matched 16,200 = exact + format + first copy of duplicates; partial 2,000 = amount + branch; missing each 800 / 1,000).
| 2 | e1c6d0b | Keep pipeline inputs out of checkpointed state; state holds results only (profile showed 60k pydantic dumps and 42k re-validations per run, plus msgpack of 40k rows per checkpoint) | 20k | pipeline end-to-end (median of 3) | 612.6 | 425.1 | −31% |
| 2 | e1c6d0b | same | 20k | throughput, invoices/sec | 32,649 | 47,043 | +44% |

Round 2 numbers are the median of three runs on the same machine; the spread across the three runs was under 2%.

| 3 | ba8d35c | Precompile invoice-number regexes and cache `canon_invoice` (profile showed it at 40% of match time: 183k module-level `re.sub`/`re.match` calls, and the same numbers canonicalised on both sides) | 20k | match (median of 3) | 251.9 | 192.2 | −24% |
| 3 | ba8d35c | same | 20k | pipeline end-to-end (median of 3) | 444.1 | 369.7 | −17% |
| 3 | ba8d35c | same | 20k | throughput, invoices/sec | 45,031 | 54,099 | +20% |

Round 3's baseline (444.1 ms) is higher than round 2's result (425.1 ms); it was measured on a different day, and the cause of the gap was not isolated. Round 3's before and after runs were taken back to back on the same machine, so the delta compares like with like.

## Real-model run (Gemini 2.5 Flash, free tier)

| Date | Commit | Size | LLM calls | Resolve stage | Pipeline | Throughput | Note |
|---|---|---|---|---|---|---|---|
| 2026-11-17 | 5fb9a30 | 100 invoices (10 partial rows) | 10 | 108,954 ms | 108,964 ms | 0.9 inv/s | Quota-bound: free tier allows 5 requests/min, so the client backed off on 429s. Not a compute measurement. |

Single-call latency measured separately: about 1.4 s for a 19-token-in, 9-token-out prompt. The gap between that and 109 s for 10 calls is the free-tier rate limit, not model time. Real throughput needs a paid tier with a higher quota; these numbers say nothing about production speed.
