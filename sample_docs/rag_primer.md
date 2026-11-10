# Retrieval-Augmented Generation Primer

Retrieval-augmented generation (RAG) combines a search step with a language model. Instead of relying only on what the model memorized during training, the system first retrieves relevant passages from a document collection and gives them to the model as context.

## Chunking

Documents are split into chunks before indexing. Chunks that are too large dilute the embedding and waste context; chunks that are too small lose meaning. A common starting point is 500 to 1000 characters with 10 to 20 percent overlap, so that sentences straddling a boundary remain retrievable.

## Embeddings and vector search

Each chunk is converted into an embedding, a vector that captures its meaning. At query time the question is embedded too, and the nearest chunks by cosine similarity are returned. This finds passages that match by meaning even when they share no keywords with the question.

## Grounding and citations

To reduce hallucination, the prompt instructs the model to answer only from the retrieved passages and to cite them. Citations let a reader verify each claim. If the passages do not contain the answer, the model should say so rather than guess.

## Evaluation

RAG quality has two parts: retrieval (did the right passage come back?) and generation (did the answer use it faithfully?). Retrieval is measured with hit rate at k, the share of questions whose correct passage appears in the top k results.
