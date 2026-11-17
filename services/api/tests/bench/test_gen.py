from collections import Counter

from benchmarks.gen import MIX, generate


def test_gen_counts_and_mix(tmp_path: object) -> None:
    from pathlib import Path

    out = Path(str(tmp_path))
    kinds = generate(out, n_invoices=1000, seed=1)
    counts = Counter(kinds)
    assert sum(counts.values()) == 1000
    for kind, share in MIX.items():
        assert counts[kind] == round(1000 * share), kind


def test_gen_deterministic(tmp_path: object) -> None:
    import hashlib
    from pathlib import Path

    a, b = Path(str(tmp_path)) / "a", Path(str(tmp_path)) / "b"
    generate(a, n_invoices=200, seed=7)
    generate(b, n_invoices=200, seed=7)
    ha = hashlib.sha256((a / "books.csv").read_bytes()).hexdigest()
    hb = hashlib.sha256((b / "books.csv").read_bytes()).hexdigest()
    assert ha == hb
