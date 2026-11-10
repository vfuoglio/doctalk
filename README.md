# DocTalk

Chat with your documents. Every answer cites its sources.

DocTalk is a small retrieval-augmented generation (RAG) app. Point it at PDFs, Markdown, or text files, then ask questions in the terminal or a web UI. Answers are grounded in your documents and carry numbered citations you can expand to see the exact passage.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
export ANTHROPIC_API_KEY=...        # needed for answers (see "No API key?" below)

doctalk ingest sample_docs          # index a file or folder
doctalk ask "How hot is Venus?"     # one-shot question
doctalk chat                        # interactive terminal Q&A
doctalk ui                          # Streamlit web app
```

Example:

```
$ doctalk ask "How hot is Venus?"
Venus is the hottest planet, with surface temperatures around 465 °C, caused by its
dense carbon dioxide atmosphere [1].

Sources:
 *[1] solar_system.md
  [2] rag_primer.md
```

`*` marks sources the answer actually cited.

### No API key?

Indexing and retrieval run locally and need no key. Add `--no-llm` to see the passages the system would hand to the model:

```bash
doctalk ingest sample_docs
doctalk ask --no-llm "How hot is Venus?"
```

Answers need an Anthropic API key (billed per use, separate from a claude.ai subscription). A question costs roughly a cent on the default model; set `DOCTALK_MODEL=claude-haiku-5-5` for a fraction of that.

## How it works

```
files ─▶ loaders ─▶ chunking ─▶ embeddings ─▶ ChromaDB
                                                  │
question ─▶ embed ─▶ top-k similar chunks ────────┘
                         │
                         ▼
         numbered excerpts + strict system prompt ─▶ Claude ─▶ answer with [n] citations
```

| Module | Role |
|---|---|
| `loaders.py` | Reads PDF (per page), Markdown, and text |
| `chunking.py` | Paragraph-aware packing with character overlap |
| `store.py` | Local persistent Chroma store; idempotent re-ingest |
| `rag.py` | Retrieval, prompt construction, streaming, citation validation |
| `cli.py`, `app.py` | Terminal and Streamlit front ends |

## Design decisions

- **Local embeddings.** Chroma's built-in MiniLM model runs on your machine, so indexing is free, offline, and keeps document contents off the network. Only the retrieved excerpts are sent to the LLM.
- **Citations you can check.** The prompt numbers each excerpt and requires `[n]` markers. Citation numbers in the answer are validated against the retrieved set, so the UI only ever shows sources that exist.
- **Refuse rather than guess.** The system prompt tells the model to say so when the excerpts don't contain the answer.
- **Idempotent ingest.** Re-indexing a file replaces its chunks, so edits don't leave stale duplicates.
- **Low reasoning effort.** Grounded Q&A over short excerpts doesn't need deep reasoning; `effort: low` keeps it fast and cheap. The model is configurable with `DOCTALK_MODEL`.

## Evaluation

Retrieval quality is measured offline, with no API key, on a small labelled question set:

```bash
python eval/run_eval.py -k 3
# hit@3: 10/10 = 100%   MRR: 0.950
```

Add your own `{"q": ..., "source": ...}` cases to `eval/questions.json` and point `--docs` at your corpus. Treat the sample numbers as a smoke test: the corpus is tiny.

## Tests

```bash
pytest
```

Covers chunking, the vector store, citation parsing, and the answer path (with a fake client, so no network).

## Limitations and next steps

- Scanned PDFs need OCR first; only embedded text is extracted.
- Pure vector search; hybrid (BM25 + vectors) and a reranker would help on keyword-heavy queries.
- Single-turn answers; follow-up questions are not yet rewritten into standalone queries.
- No LLM-judged faithfulness eval yet, only retrieval metrics.

## License

MIT
