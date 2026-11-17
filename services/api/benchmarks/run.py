"""Benchmark runner: times the real pipeline on generated load, writes one JSON per run.

Usage: uv run python -m benchmarks.run --size 1000 --llm fake
Measures speed only. Accuracy is never scored on synthetic data.
"""

import argparse
import json
import os
import subprocess
import tempfile
import time
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from app.agents.llm import FakeLLM, VertexLLM
from app.agents.roles import ResolverOut
from app.guard.budget import Budget
from app.ingest.books import parse_books
from app.ingest.gstr2b import parse_gstr2b_json
from app.pipeline.graph import Deps, run_pipeline
from benchmarks.gen import generate

RESULTS = Path(__file__).parent / "results"


def _sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "nogit"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", type=int, default=1000)
    parser.add_argument("--llm", choices=["fake", "gemini"], default="fake")
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        t0 = time.perf_counter()
        generate(base, n_invoices=args.size, seed=args.seed)
        gen_ms = (time.perf_counter() - t0) * 1000

        t1 = time.perf_counter()
        gs = parse_gstr2b_json((base / "gstr2b.json").read_bytes())
        bs = parse_books((base / "books.csv").read_bytes(), "books.csv")
        ingest_ms = (time.perf_counter() - t1) * 1000

    llm: FakeLLM | VertexLLM
    if args.llm == "gemini":
        llm = VertexLLM(api_key=os.environ["GEMINI_API_KEY"])
    else:
        llm = FakeLLM(
            {
                ResolverOut: ResolverOut(
                    row_key="x",
                    likely_cause="unknown",
                    explanation="bench",
                    suggested_action="none",
                )
            }
        )
    deps = Deps(llm=llm, budget=Budget(10**12, Decimal(10**9)), firm_id="bench")
    t2 = time.perf_counter()
    state = run_pipeline(f"bench-{time.time_ns()}", gs, bs, "2026-11", deps)
    e2e_ms = (time.perf_counter() - t2) * 1000

    timings = state.get("timings", {})
    counts: dict[str, int] = {}
    for r in state["results"]:
        counts[str(r["verdict"])] = counts.get(str(r["verdict"]), 0) + 1
    report = {
        "when": datetime.now(UTC).isoformat(timespec="seconds"),
        "sha": _sha(),
        "size_invoices": args.size,
        "llm": args.llm,
        "stage_ms": {
            "generate": round(gen_ms, 1),
            "ingest": round(ingest_ms, 1),
            **{k: round(v, 1) for k, v in timings.items()},
        },
        "pipeline_ms": round(e2e_ms, 1),
        "invoices_per_sec": round(args.size / max(e2e_ms / 1000, 1e-9), 1),
        "llm_calls": len(llm.calls) if isinstance(llm, FakeLLM) else None,
        "counts_by_verdict": counts,
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    name = f"{report['when'].replace(':', '')}-{report['sha']}-{args.size}.json"
    (RESULTS / name).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
