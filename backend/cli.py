"""Terminal client for the MarketPulse agent. Built for live demos:
every tool call, tool result and summarization event is printed as
it happens, so the class can watch the agent think.

Note that this file imports the SAME graph as the API. CLI and web UI
are just two doors into one brain, and because the checkpointer lives
in Postgres, a conversation started here can be continued in the UI.

Run:  just cli              (or: uv run python -m backend.cli)
      just cli my-demo      (named thread)

Inside the chat:
  /state     show message count and current summary
  /history   show the saved conversation
  /threads   list all threads in the checkpointer
  /quit      exit (the conversation survives, that is the point)
"""
import argparse
import json

from langchain_core.messages import HumanMessage
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from . import config, memory
from .graph import build_graph

console = Console()


def show_state(graph, cfg):
    snapshot = graph.get_state(cfg)
    values = snapshot.values or {}
    n = len(values.get("messages", []))
    summary = values.get("summary", "")
    console.print(f"[bold]messages in state:[/bold] {n}")
    console.print(f"[bold]summary:[/bold] {summary or '(none yet, conversation is short)'}")


def show_history(graph, cfg):
    snapshot = graph.get_state(cfg)
    for m in snapshot.values.get("messages", []):
        if m.type == "human":
            console.print(f"[cyan]you:[/cyan] {m.content}")
        elif m.type == "ai" and m.content:
            console.print(f"[green]agent:[/green] {m.content[:200]}")


def run_turn(graph, cfg, text: str):
    """Stream the graph and narrate every step.

    graph.stream(..., stream_mode="updates") yields one event per node
    as it finishes: {"summarize": {...}}, {"agent": {...}}, {"tools": {...}}.
    We pattern-match on the node name to narrate what just happened.
    This is the same data the checkpointer is saving snapshot-by-snapshot.
    """
    for update in graph.stream(
        {"messages": [HumanMessage(content=text)]}, cfg, stream_mode="updates"
    ):
        for node, payload in update.items():
            if node == "summarize" and payload:
                console.print(Panel(
                    payload.get("summary", "")[:400],
                    title="summarize node fired: old messages folded into summary",
                    border_style="magenta",
                ))
            elif node == "agent":
                msg = payload["messages"][-1]
                for call in getattr(msg, "tool_calls", []):
                    args = json.dumps(call["args"])
                    console.print(f"[yellow]  -> tool call: {call['name']}({args})[/yellow]")
                if msg.content:
                    console.print(Panel(Markdown(msg.content), title="agent", border_style="green"))
            elif node == "tools":
                for msg in payload["messages"]:
                    preview = str(msg.content)[:160]
                    console.print(f"[dim]  <- {msg.name}: {preview}...[/dim]")


def main():
    parser = argparse.ArgumentParser(description="MarketPulse CLI")
    parser.add_argument("--thread", default="cli-demo", help="thread id (a conversation)")
    args = parser.parse_args()

    checkpointer = memory.get_checkpointer()
    graph = build_graph(checkpointer)
    cfg = {"configurable": {"thread_id": args.thread}}

    mode = "MOCK (fixtures)" if config.OXYLABS_MOCK else "LIVE (Oxylabs)"
    console.print(Panel(
        f"thread: [bold]{args.thread}[/bold]   scraping: [bold]{mode}[/bold]\n"
        "commands: /state  /history  /threads  /quit",
        title="MarketPulse agent",
        border_style="blue",
    ))

    while True:
        try:
            text = console.input("[bold cyan]you> [/bold cyan]").strip()
        except (KeyboardInterrupt, EOFError):
            break
        if not text:
            continue
        if text == "/quit":
            break
        if text == "/state":
            show_state(graph, cfg)
            continue
        if text == "/history":
            show_history(graph, cfg)
            continue
        if text == "/threads":
            console.print(memory.list_threads(checkpointer))
            continue
        run_turn(graph, cfg, text)

    console.print("bye. your conversation is saved in the checkpointer.")


if __name__ == "__main__":
    main()
