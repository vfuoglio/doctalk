from pathlib import Path

from doctalk.store import Store

DOCS = Path(__file__).parent.parent / "sample_docs"


def test_ingest_and_search(tmp_path):
    store = Store(tmp_path / "db")
    counts = store.ingest(DOCS)
    assert set(counts) == {"rag_primer.md", "sourdough.txt", "solar_system.md"}

    hit = store.search("how hot is Venus?", k=1)[0]
    assert hit.source == "solar_system.md"

    hit = store.search("how often should I feed my starter", k=1)[0]
    assert hit.source == "sourdough.txt"


def test_reingest_does_not_duplicate(tmp_path):
    store = Store(tmp_path / "db")
    store.ingest(DOCS)
    n = store.count()
    store.ingest(DOCS)
    assert store.count() == n


def test_empty_store_search(tmp_path):
    assert Store(tmp_path / "db").search("anything") == []


def test_cli_no_llm_needs_no_key(tmp_path, capsys, monkeypatch):
    from doctalk.cli import main

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    db = str(tmp_path / "db")
    assert main(["--db", db, "ingest", str(DOCS)]) == 0
    assert main(["--db", db, "ask", "--no-llm", "how hot is Venus?", "-k", "1"]) == 0
    assert "solar_system.md" in capsys.readouterr().out


def test_cli_ask_without_key_explains(tmp_path, capsys, monkeypatch):
    from doctalk.cli import main

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert main(["--db", str(tmp_path / "db"), "ask", "hi"]) == 1
    assert "--no-llm" in capsys.readouterr().out
