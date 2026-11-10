"""Retrieval eval: hit rate @ k and MRR over eval/questions.json.

Offline (no API key needed). Usage: python eval/run_eval.py [--docs sample_docs] [-k 3]
"""
import argparse
import json
import tempfile
from pathlib import Path

from doctalk.store import Store

ROOT = Path(__file__).parent.parent


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--docs", default=str(ROOT / "sample_docs"))
    p.add_argument("--questions", default=str(Path(__file__).with_name("questions.json")))
    p.add_argument("-k", type=int, default=3)
    a = p.parse_args()

    cases = json.loads(Path(a.questions).read_text())
    with tempfile.TemporaryDirectory() as tmp:
        store = Store(tmp)
        store.ingest(a.docs)
        hits_at_k, rr = 0, 0.0
        for c in cases:
            sources = [h.source for h in store.search(c["q"], k=a.k)]
            if c["source"] in sources:
                hits_at_k += 1
                rr += 1 / (sources.index(c["source"]) + 1)
            else:
                print(f"MISS: {c['q']!r} -> {sources}")
    n = len(cases)
    print(f"hit@{a.k}: {hits_at_k}/{n} = {hits_at_k / n:.0%}   MRR: {rr / n:.3f}")


if __name__ == "__main__":
    main()
