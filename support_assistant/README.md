# Support Assistant Module

This module implements a grounded Zepto policy QA system with a fully offline mock path by default.

## Architecture

The pipeline runs in this order:

1. Ingestion: all eight Zepto policy documents are read from `support_assistant/docs/`.
2. Embedding: each chunk is embedded with the `all-MiniLM-L6-v2` sentence-transformer model and stored in a ChromaDB collection.
3. Retrieval: the `retrieve_and_answer` graph node embeds the user query, retrieves the top 3 most similar chunks, and uses the strongest match for the mock answer.
4. Generation: the final answer is produced by the `retrieve_and_answer` or `direct_answer` node, depending on the intent route. In mock mode, this path uses deterministic templated responses instead of an LLM call.

The `classify_intent` node is the router and decides whether the question is a policy question or a general question. The graph is built with a LangGraph `StateGraph` and uses a conditional edge.

## MCQ demo examples

With `MOCK_LLM` left at its default, the app routes:

- `"How long does Zepto delivery take?"` -> `policy_question`
- `"Who won the latest cricket match?"` -> `general_question`

## Run

```bash
cd support_assistant
python main.py
```

And then `curl` the local API:

```bash
curl -X POST http://127.0.0.1:8000/ask -H "Content-Type: application/json" -d '{"query":"What is Zepto's delivery policy?"}'
```

## Docker

```bash
docker build -t zepto-support-assistant .
docker run -p 7860:7860 zepto-support-assistant
```
