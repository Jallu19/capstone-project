from __future__ import annotations

import os
from pathlib import Path
from typing import TypedDict

import chromadb
from fastapi import FastAPI
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer

MOCK_LLM = os.getenv("MOCK_LLM", "1")
BASE_DIR = Path(__file__).resolve().parent
DOCS_DIR = BASE_DIR / "docs"
CHROMA_DIR = BASE_DIR / "chroma_store"
MODEL_NAME = "all-MiniLM-L6-v2"


class AskRequest(BaseModel):
    query: str


class AskResponse(BaseModel):
    answer: str
    sources: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class State(TypedDict):
    query: str
    intent: str
    results: list[dict]
    final_answer: str
    sources: list[str]
    confidence: float


def load_documents() -> list[tuple[str, str]]:
    docs = []
    for path in sorted(DOCS_DIR.glob("doc_*.txt")):
        text = path.read_text(encoding="utf-8")
        docs.append((path.stem, text))
    return docs


class SupportGraph:
    def __init__(self) -> None:
        self.client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        self.collection = self.client.get_or_create_collection(name="zepto_policy")
        self.model = SentenceTransformer(MODEL_NAME)
        self._index_documents()

    def _index_documents(self) -> None:
        docs = load_documents()
        if self.collection.count() == 0:
            ids = [doc_id for doc_id, _ in docs]
            chunks = [text for _, text in docs]
            embeddings = self.model.encode(chunks, convert_to_numpy=True, normalize_embeddings=True)
            self.collection.add(ids=ids, documents=chunks, embeddings=embeddings.tolist())

    def classify_intent(self, state: State) -> State:
        q = state["query"].lower()
        policy_keywords = ["delivery", "return", "refund", "membership", "tracking", "cancel", "gift card", "support hours"]
        intent = "policy_question" if any(keyword in q for keyword in policy_keywords) else "general_question"
        state["intent"] = intent
        return state

    def retrieve_and_answer(self, state: State) -> State:
        query = state["query"]
        embeddings = self.model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
        hits = self.collection.query(query_embeddings=embeddings.tolist(), n_results=3)
        docs = hits["documents"][0]
        ids = hits["ids"][0]
        top_doc = docs[0] if docs else "No relevant policy context found."
        snippet = top_doc[:200]
        if str(MOCK_LLM).strip().lower() not in {"0", "false"}:
            state["final_answer"] = f"Based on the retrieved context: {snippet}"
            state["sources"] = ids
            state["confidence"] = 1.0
        else:
            state["final_answer"] = f"Based on the retrieved context: {snippet}"
            state["sources"] = ids
            state["confidence"] = 1.0
        state["results"] = [{"id": doc_id, "content": doc} for doc_id, doc in zip(ids, docs)]
        return state

    def direct_answer(self, state: State) -> State:
        state["final_answer"] = "I can only answer questions about Zepto policies right now."
        state["sources"] = []
        state["confidence"] = 1.0
        return state

    def build_graph(self):
        graph = StateGraph(State)
        graph.add_node("classify_intent", self.classify_intent)
        graph.add_node("retrieve_and_answer", self.retrieve_and_answer)
        graph.add_node("direct_answer", self.direct_answer)
        graph.add_conditional_edges(
            "classify_intent",
            lambda s: "retrieve_and_answer" if s["intent"] == "policy_question" else "direct_answer",
        )
        graph.set_entry_point("classify_intent")
        graph.add_edge("retrieve_and_answer", END)
        graph.add_edge("direct_answer", END)
        return graph.compile()


app = FastAPI(title="Zepto Support Assistant")


def create_response(answer: str, sources: list[str], confidence: float) -> AskResponse:
    return AskResponse(answer=answer, sources=sources, confidence=confidence)


@app.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest) -> AskResponse:
    graph = SupportGraph().build_graph()
    state = {"query": payload.query, "intent": "", "results": [], "final_answer": "", "sources": [], "confidence": 0.0}
    result = graph.invoke(state)
    return create_response(result["final_answer"], result["sources"], float(result["confidence"]))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
