import asyncio
from types import SimpleNamespace
from typing import Any

from pydantic import BaseModel

from app.agents.llm import VertexLLM


class Verdict(BaseModel):
    ok: bool


class _FakeModels:
    def __init__(self, text: str, in_tok: int, out_tok: int) -> None:
        self.text, self.in_tok, self.out_tok = text, in_tok, out_tok
        self.calls: list[dict[str, Any]] = []

    async def generate_content(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        usage = SimpleNamespace(prompt_token_count=self.in_tok, candidates_token_count=self.out_tok)
        return SimpleNamespace(text=self.text, usage_metadata=usage)


class _FakeClient:
    def __init__(self, models: _FakeModels) -> None:
        self.aio = SimpleNamespace(models=models)


def test_vertex_llm_parses_schema_and_counts_usage() -> None:
    models = _FakeModels('{"ok": true}', in_tok=1000, out_tok=500)
    llm = VertexLLM(client=_FakeClient(models))
    out, usage = asyncio.run(llm.structured("gemini-2.5-flash", "sys", "user", Verdict))
    assert out == Verdict(ok=True)
    assert usage.input_tokens == 1000 and usage.output_tokens == 500
    assert usage.inr > 0
    cfg = models.calls[0]["config"]
    assert cfg.response_mime_type == "application/json"


def test_gemini_api_key_client_uses_key_not_vertex() -> None:
    llm = VertexLLM(api_key="test-key")
    assert llm._client._api_client.api_key == "test-key"  # type: ignore[attr-defined]
    assert not llm._client._api_client.vertexai  # type: ignore[attr-defined]


def test_retries_on_quota_then_succeeds(monkeypatch: object) -> None:
    from google.genai import errors

    import app.agents.llm as llm_mod

    async def no_sleep(_: float) -> None:
        return None

    monkeypatch.setattr(llm_mod.asyncio, "sleep", no_sleep)  # type: ignore[attr-defined]

    calls = {"n": 0}

    class _Models:
        async def generate_content(self, **_: Any) -> Any:
            calls["n"] += 1
            if calls["n"] < 3:
                raise errors.ClientError(429, {"error": {"message": "quota"}}, None)
            return SimpleNamespace(
                text='{"ok": true}',
                usage_metadata=SimpleNamespace(prompt_token_count=1, candidates_token_count=1),
            )

    llm = VertexLLM(client=SimpleNamespace(aio=SimpleNamespace(models=_Models())))
    out, _ = asyncio.run(llm.structured("gemini-2.5-flash", "s", "u", Verdict))
    assert out == Verdict(ok=True)
    assert calls["n"] == 3
