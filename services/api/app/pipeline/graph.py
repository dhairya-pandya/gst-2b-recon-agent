import asyncio
from dataclasses import dataclass, field
from typing import Any, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from app.agents.critic import check_output
from app.agents.llm import LLM, stage
from app.agents.roles import resolve, row_key
from app.core.match import MatchResult, Verdict, match
from app.guard.budget import Budget
from app.models import BookRow, Gstr2bRow

RESOLVE_CONCURRENCY = 8


@dataclass
class Deps:
    llm: LLM
    budget: Budget
    firm_id: str
    checkpointer: MemorySaver = field(default_factory=MemorySaver)
    match_calls: int = 0


class PipelineState(TypedDict, total=False):
    gstr2b: list[dict[str, Any]]
    books: list[dict[str, Any]]
    period: str
    results: list[dict[str, Any]]
    agent_outputs: dict[str, dict[str, Any]]
    timings: dict[str, float]
    degraded: bool


def _build(deps: Deps) -> Any:
    def match_node(state: PipelineState) -> dict[str, Any]:
        deps.match_calls += 1
        gs = [Gstr2bRow.model_validate(r) for r in state["gstr2b"]]
        bs = [BookRow.model_validate(b) for b in state["books"]]
        timings = dict(state.get("timings", {}))
        with stage("match", timings):
            results = match(gs, bs, state["period"])
        return {
            "results": [{**r.model_dump(mode="json"), "key": row_key(r)} for r in results],
            "timings": timings,
        }

    def resolve_node(state: PipelineState) -> dict[str, Any]:
        timings = dict(state.get("timings", {}))
        outputs: dict[str, dict[str, Any]] = {}
        results = [dict(r) for r in state["results"]]
        degraded = False

        async def one(r: dict[str, Any]) -> None:
            nonlocal degraded
            key = str(r["key"])
            if not deps.budget.allow(deps.firm_id):
                degraded = True
                r["needs_review"] = True
                return
            m = MatchResult.model_validate(r)
            out, usage = await resolve(deps.llm, m, "")
            deps.budget.charge(deps.firm_id, usage)
            outputs[key] = out.model_dump()

        sem = asyncio.Semaphore(RESOLVE_CONCURRENCY)

        async def guarded(r: dict[str, Any]) -> None:
            async with sem:
                await one(r)

        targets = [r for r in results if r["verdict"] == Verdict.PARTIAL.value]
        with stage("resolve", timings):
            asyncio.run(_gather(guarded, targets))
        return {
            "agent_outputs": outputs,
            "results": results,
            "degraded": degraded,
            "timings": timings,
        }

    def critic_node(state: PipelineState) -> dict[str, Any]:
        timings = dict(state.get("timings", {}))
        results = [dict(r) for r in state["results"]]
        with stage("critic", timings):
            for r in results:
                key = str(r["key"])
                out = state.get("agent_outputs", {}).get(key)
                if out is None:
                    continue
                m = MatchResult.model_validate(r)
                problems = check_output(out["explanation"], [], m, set())
                if problems:
                    r["needs_review"] = True
                    r["problems"] = problems
        return {"results": results, "timings": timings}

    g: StateGraph[PipelineState] = StateGraph(PipelineState)
    g.add_node("match", match_node)
    g.add_node("resolve", resolve_node)
    g.add_node("critic", critic_node)
    g.add_edge(START, "match")
    g.add_edge("match", "resolve")
    g.add_edge("resolve", "critic")
    g.add_edge("critic", END)
    return g.compile(checkpointer=deps.checkpointer)


async def _gather(fn: Any, items: list[dict[str, Any]]) -> None:
    await asyncio.gather(*(fn(i) for i in items))


def run_pipeline(
    thread_id: str,
    gstr2b: list[Gstr2bRow],
    books: list[BookRow],
    period: str,
    deps: Deps,
) -> PipelineState:
    graph = _build(deps)
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = graph.get_state(config)
    if snapshot.values and not snapshot.next:
        return PipelineState(**snapshot.values)  # finished: return saved result, no rerun
    payload: dict[str, Any] | None = None
    if not snapshot.values:
        payload = {
            "gstr2b": [r.model_dump(mode="json") for r in gstr2b],
            "books": [b.model_dump(mode="json") for b in books],
            "period": period,
        }
    result: PipelineState = graph.invoke(payload, config)
    return result
