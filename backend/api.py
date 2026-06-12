"""FastAPI app: the HTTP layer around the agent.

This file contains NO agent logic. It only:
  - builds the graph once at startup (lifespan)
  - translates HTTP requests into graph.invoke() calls
  - extracts structured data from tool results so the UI can draw
    product cards and image galleries instead of plain text

Endpoints:
  POST /chat                      talk to the agent on a thread
  GET  /threads                   list known threads
  GET  /threads/{id}/history      full message history of a thread
  GET  /threads/{id}/state        summary + message count (for the UI panel)
  /downloads/*                    downloaded product images (static files)

Run:  just backend   (or: uv run uvicorn backend.api:app --port 8010)
"""
import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from . import config, memory
from .graph import build_graph

logging.basicConfig(level=logging.INFO)

graph = None
checkpointer = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global graph, checkpointer
    checkpointer = memory.get_checkpointer()
    graph = build_graph(checkpointer)
    yield


app = FastAPI(title="MarketPulse API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/downloads", StaticFiles(directory=config.DOWNLOADS_DIR), name="downloads")


class ChatRequest(BaseModel):
    thread_id: str
    message: str


def _collect_turn_artifacts(messages, user_message: str):
    """Walk backwards over this turn's messages and pull out structured
    tool results (products, images) plus the list of tool calls made,
    so the UI can render rich cards instead of plain text."""
    tool_calls, products, images = [], [], []

    for m in reversed(messages):
        if m.type == "human" and m.content == user_message:
            break
        if m.type == "ai":
            for call in getattr(m, "tool_calls", []):
                tool_calls.append({"name": call["name"], "args": call["args"]})
        if m.type == "tool":
            try:
                data = json.loads(m.content)
            except (json.JSONDecodeError, TypeError):
                continue
            if "products" in data:
                products.extend(data["products"])
            if "product" in data:
                products.append(data["product"])
            if "competitors" in data:
                products.extend(data["competitors"])
            if "downloaded" in data:
                images.append(
                    {"asin": data.get("asin"), "title": data.get("title"),
                     "paths": data["downloaded"]}
                )

    tool_calls.reverse()
    products.reverse()

    seen, unique_products = set(), []
    for p in products:
        if p.get("asin") and p["asin"] not in seen:
            seen.add(p["asin"])
            unique_products.append(p)
    return tool_calls, unique_products, images


@app.post("/chat")
def chat(req: ChatRequest):
    # The thread_id in the config is THE memory key. Same thread_id ->
    # the checkpointer loads the saved state and the conversation
    # continues. New thread_id -> blank conversation. This one dict is
    # the entire multi-user story.
    cfg = {"configurable": {"thread_id": req.thread_id}}
    try:
        result = graph.invoke({"messages": [HumanMessage(content=req.message)]}, cfg)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    reply = result["messages"][-1].content
    tool_calls, products, images = _collect_turn_artifacts(result["messages"], req.message)

    return {
        "thread_id": req.thread_id,
        "reply": reply,
        "tool_calls": tool_calls,
        "products": products,
        "images": images,
        "summary": result.get("summary", ""),
        "message_count": len(result["messages"]),
    }


@app.get("/threads")
def threads():
    return {"threads": memory.list_threads(checkpointer)}


@app.get("/threads/{thread_id}/history")
def history(thread_id: str):
    cfg = {"configurable": {"thread_id": thread_id}}
    snapshot = graph.get_state(cfg)
    out = []
    for m in snapshot.values.get("messages", []):
        if m.type in ("human", "ai") and m.content:
            out.append({"role": "user" if m.type == "human" else "assistant",
                        "content": m.content})
    return {"thread_id": thread_id, "messages": out}


@app.get("/threads/{thread_id}/state")
def thread_state(thread_id: str):
    cfg = {"configurable": {"thread_id": thread_id}}
    snapshot = graph.get_state(cfg)
    values = snapshot.values or {}
    return {
        "thread_id": thread_id,
        "summary": values.get("summary", ""),
        "message_count": len(values.get("messages", [])),
        "checkpoints": len(list(graph.get_state_history(cfg))),
    }


@app.get("/health")
def health():
    return {"status": "ok", "mock_mode": config.OXYLABS_MOCK}
