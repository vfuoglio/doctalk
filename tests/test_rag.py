from doctalk.rag import build_context, cited_numbers
from doctalk.store import Hit


def test_cited_numbers_filters_invalid_and_dedupes():
    assert cited_numbers("Yes [1][3]. Also [1] and [9] and [0].", 3) == [1, 3]


def test_cited_numbers_none():
    assert cited_numbers("I could not find that.", 5) == []


def test_build_context_numbers_sources():
    hits = [Hit("first", "a.md", "", 0.1), Hit("second", "b.pdf", "p. 2", 0.2)]
    ctx = build_context(hits)
    assert "[1] (a.md)\nfirst" in ctx
    assert "[2] (b.pdf (p. 2))\nsecond" in ctx


class _FakeStream:
    def __init__(self, parts):
        self.text_stream = iter(parts)

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class _FakeClient:
    def __init__(self):
        self.calls = []
        self.messages = self

    def stream(self, **kw):
        self.calls.append(kw)
        return _FakeStream(["Venus is hot ", "[1]."])


def test_answer_streams_and_grounds_prompt(tmp_path):
    from pathlib import Path

    from doctalk.rag import answer
    from doctalk.store import Store

    store = Store(tmp_path / "db")
    store.ingest(Path(__file__).parent.parent / "sample_docs")
    client = _FakeClient()

    result = answer("How hot is Venus?", store, k=2, client=client)

    assert result.text == "Venus is hot [1]."
    assert result.cited == [1]
    sent = client.calls[0]["messages"][-1]["content"]
    assert "Sources:" in sent and "465 degrees" in sent
    assert "ONLY" in client.calls[0]["system"]
