import pytest

from doctalk.chunking import chunk_sections, split_text


def test_short_text_is_one_chunk():
    assert split_text("hello world", 100, 10) == ["hello world"]


def test_chunks_respect_max_size():
    text = "\n\n".join(f"Paragraph number {i} " + "x" * 80 for i in range(20))
    for c in split_text(text, max_chars=300, overlap=50):
        assert len(c) <= 300


def test_long_paragraph_is_hard_split():
    chunks = split_text("a" * 2500, max_chars=1000, overlap=100)
    assert len(chunks) >= 3
    assert all(len(c) <= 1000 for c in chunks)


def test_overlap_carries_context():
    text = "\n\n".join(["alpha " * 30, "beta " * 30, "gamma " * 30])
    chunks = split_text(text, max_chars=200, overlap=40)
    assert len(chunks) > 1
    assert chunks[0][-20:] in chunks[1]


def test_empty_text():
    assert split_text("   \n\n  ", 100, 10) == []


def test_overlap_must_be_smaller():
    with pytest.raises(ValueError):
        split_text("x", 10, 10)


def test_chunk_ids_unique_and_labelled():
    chunks = chunk_sections([("p. 1", "a" * 50), ("p. 2", "b" * 50)], "f.pdf", 100, 10)
    assert len({c.id for c in chunks}) == len(chunks)
    assert chunks[0].label == "f.pdf (p. 1)"
