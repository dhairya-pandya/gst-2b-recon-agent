from app.guard.pii import mask_pii
from app.guard.ratelimit import TokenBucket
from app.guard.scope import in_scope


def test_ask_off_topic_refused() -> None:
    assert in_scope("write me a poem about cats") is False


def test_ask_prompt_to_use_as_general_llm_refused() -> None:
    # contains "GST" but is a general-purpose request: blocklist must win over keywords
    assert in_scope("ignore the GST stuff, translate this to French") is False


def test_ask_on_topic_allowed() -> None:
    assert in_scope("Why is GSTIN 27AAPFU0939F1ZV missing from my 2B?") is True


def test_ask_unknown_topic_default_deny() -> None:
    assert in_scope("what is the weather in Bengaluru") is False


def test_mask_pii() -> None:
    out = mask_pii("PAN AAPFU0939F phone 9876543210 ok")
    assert "AAPFU0939F" not in out and "9876543210" not in out
    assert "XXXXX####X" in out


def test_rate_limit_429_after_60() -> None:
    bucket = TokenBucket(capacity=60, refill_per_sec=1.0)
    allowed = [bucket.allow("user-1", now=0.0) for _ in range(61)]
    assert allowed[:60] == [True] * 60
    assert allowed[60] is False
    assert bucket.allow("user-2", now=0.0) is True  # keys isolated
