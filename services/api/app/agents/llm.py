import time
from collections.abc import Iterator
from contextlib import contextmanager
from decimal import Decimal
from typing import Any, Protocol, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

# INR per 1M tokens (input, output). Placeholder values: verify against current
# Vertex AI pricing before any cost figure is published.
PRICES: dict[str, tuple[Decimal, Decimal]] = {
    "gemini-2.5-flash": (Decimal("25"), Decimal("210")),
    "gemini-2.5-pro": (Decimal("105"), Decimal("840")),
}


class Usage(BaseModel):
    input_tokens: int
    output_tokens: int
    latency_ms: float
    inr: Decimal


class LLM(Protocol):
    async def structured(
        self, model: str, system: str, user: str, schema: type[T]
    ) -> tuple[T, Usage]: ...


def cost_inr(
    model: str,
    input_tokens: int,
    output_tokens: int,
    prices: dict[str, tuple[Decimal, Decimal]] | None = None,
) -> Decimal:
    table = PRICES if prices is None else prices
    p_in, p_out = table[model]
    total = (Decimal(input_tokens) * p_in + Decimal(output_tokens) * p_out) / Decimal(1_000_000)
    return total.quantize(Decimal("0.000001"))


class FakeLLM:
    """Deterministic stand-in for tests and CI benchmarks. Never calls a network."""

    def __init__(self, responses: dict[type[BaseModel], BaseModel]) -> None:
        self.responses = responses
        self.calls: list[dict[str, Any]] = []

    async def structured(
        self, model: str, system: str, user: str, schema: type[T]
    ) -> tuple[T, Usage]:
        self.calls.append({"model": model, "system": system, "user": user})
        value = self.responses[schema]
        assert isinstance(value, schema)
        usage = Usage(
            input_tokens=len(system + user) // 4,
            output_tokens=len(value.model_dump_json()) // 4,
            latency_ms=0.0,
            inr=Decimal("0"),
        )
        return value, usage


@contextmanager
def stage(name: str, timings: dict[str, float]) -> Iterator[None]:
    start = time.perf_counter()
    try:
        yield
    finally:
        timings[name] = timings.get(name, 0.0) + (time.perf_counter() - start) * 1000


class VertexLLM:
    """Gemini via Vertex AI (google-genai SDK). Requires GCP project and ADC credentials."""

    def __init__(
        self, client: Any | None = None, project: str | None = None, location: str = "asia-south1"
    ) -> None:
        if client is None:
            from google import genai

            client = genai.Client(vertexai=True, project=project, location=location)
        self._client = client

    async def structured(
        self, model: str, system: str, user: str, schema: type[T]
    ) -> tuple[T, Usage]:
        from google.genai import types

        start = time.perf_counter()
        resp = await self._client.aio.models.generate_content(
            model=model,
            contents=user,
            config=types.GenerateContentConfig(
                system_instruction=system,
                response_mime_type="application/json",
                response_schema=schema,
                temperature=0,
            ),
        )
        latency = (time.perf_counter() - start) * 1000
        value = schema.model_validate_json(resp.text or "")
        meta = resp.usage_metadata
        in_tok = int(getattr(meta, "prompt_token_count", 0) or 0)
        out_tok = int(getattr(meta, "candidates_token_count", 0) or 0)
        usage = Usage(
            input_tokens=in_tok,
            output_tokens=out_tok,
            latency_ms=latency,
            inr=cost_inr(model, in_tok, out_tok),
        )
        return value, usage
