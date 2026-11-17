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
