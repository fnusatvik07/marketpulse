"""The MarketPulse agent graph. This is the heart of the project.

The shape of the graph:

    START ──► summarize ──► agent ◄──► tools
                              │
                              ▼
                             END

  summarize  Manages SHORT-TERM MEMORY. If the conversation has grown
             too long, it folds old messages into a running summary and
             deletes them from state. Built by hand in concepts/02.

  agent      The brain. An LLM with tools bound to it. It looks at the
             conversation and either calls a tool or writes the final
             answer. It never scrapes anything itself; it only decides.

  tools      Executes whichever tool the agent asked for (search,
             product details, competitors, image download) and puts the
             result back into the conversation as a ToolMessage.

The agent ◄──► tools loop is the ReAct pattern: the agent can call a
tool, read the result, and decide to call another one, as many times
as it needs, before answering.
"""
from langchain_core.messages import HumanMessage, RemoveMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from . import config, oxylabs_client
from .tools import ALL_TOOLS


# ---------------------------------------------------------------------------
# 1. STATE
# ---------------------------------------------------------------------------
# MessagesState already gives us `messages` (a list that appends on every
# update, and understands RemoveMessage deletions).
# We add ONE extra field: the running summary of older conversation.
class State(MessagesState):
    summary: str


# One LLM client for the whole module.
# - `llm` is used for summarization (no tools needed there)
# - `llm_with_tools` is the same model with our 4 tools bound, so it can
#   emit tool calls. bind_tools() is what turns a chatbot into an agent.
llm = ChatOpenAI(model=config.OPENAI_MODEL, temperature=0)
llm_with_tools = llm.bind_tools(ALL_TOOLS)


SYSTEM_PROMPT = """You are MarketPulse, an expert e-commerce market analyst.
You help sellers research products, prices and competitors on Amazon ({domain}).

Rules:
- Use your tools to fetch real data before answering. Never invent prices.
- Quote prices with their currency.
- When comparing products, present a short table or bullet list.
- After downloading images, tell the user the images are now visible in the app.
- Be concise and analytical, like a sharp colleague, not a brochure."""


def _transcript(messages) -> str:
    """Render messages as plain text for the summarizer prompt.

    Why not just pass the message objects to the LLM? Because old messages
    include tool calls and tool results, and the OpenAI API enforces strict
    ordering rules on those (a tool message must follow its tool call).
    A plain-text transcript sidesteps all of that.
    """
    lines = []
    for m in messages:
        if m.type == "human":
            lines.append(f"user: {m.content}")
        elif m.type == "ai":
            if m.content:
                lines.append(f"assistant: {m.content[:300]}")
            for call in getattr(m, "tool_calls", []):
                lines.append(f"assistant called tool {call['name']}({call['args']})")
        elif m.type == "tool":
            lines.append(f"tool result: {str(m.content)[:300]}")
    return "\n".join(lines)


def _repair_removes(messages):
    """Find messages that would make the OpenAI API reject the request, and
    return RemoveMessage ops to delete them.

    The API rule: every assistant message with tool_calls MUST be followed by
    a tool message for each call id. If a previous turn crashed after the
    agent asked for a tool but before the tool result was saved, the thread is
    left with a 'dangling' tool call and every later turn fails with a 400.
    We heal it by dropping the dangling assistant message (and any partial
    tool replies to it).
    """
    answered = {m.tool_call_id for m in messages if m.type == "tool"}
    dangling_ai_ids, dangling_call_ids = set(), set()
    for m in messages:
        if m.type == "ai" and getattr(m, "tool_calls", None):
            call_ids = [tc["id"] for tc in m.tool_calls]
            if not all(cid in answered for cid in call_ids):
                dangling_ai_ids.add(m.id)
                dangling_call_ids.update(call_ids)

    if not dangling_ai_ids:
        return []

    removes = [RemoveMessage(id=mid) for mid in dangling_ai_ids]
    # also drop any tool messages that answered the removed assistant message,
    # so we never leave an orphaned tool message behind
    for m in messages:
        if m.type == "tool" and m.tool_call_id in dangling_call_ids:
            removes.append(RemoveMessage(id=m.id))
    return removes


# ---------------------------------------------------------------------------
# 2. THE SUMMARIZATION NODE  (short-term memory management)
# ---------------------------------------------------------------------------
def summarize_node(state: State):
    """Compress old messages into a running summary when the thread gets long.

    Runs at the START of every turn. Three steps:

      1. TRIGGER   if the history is short, do nothing (return {})
      2. SPLIT     old messages -> to be summarized
                   recent messages -> kept verbatim for the agent
      3. COMPRESS  ask the LLM to fold the old messages into the existing
                   summary, then DELETE them from state with RemoveMessage

    The facts survive inside `summary`; the bulk is gone. That keeps the
    context window (and the bill) roughly constant forever.
    """
    messages = state["messages"]

    # 0. REPAIR: heal any dangling tool call left by a previous crashed turn,
    # otherwise the OpenAI API rejects the whole thread. Apply the removals to
    # our local copy too so summarization below works on the clean history.
    repair = _repair_removes(messages)
    if repair:
        gone = {r.id for r in repair}
        messages = [m for m in messages if m.id not in gone]

    # 1. TRIGGER: nothing to do while the conversation is short.
    if len(messages) <= config.MAX_MESSAGES:
        return {"messages": repair} if repair else {}

    # 2. SPLIT: keep the last KEEP_LAST messages... but never cut in the
    # middle of a tool-call sequence. We slide the cut point forward until
    # it lands on a HumanMessage, so an AI tool call and its ToolMessage
    # result are never separated. (The last message is always the user's
    # new question, so a HumanMessage is guaranteed to be found.)
    cut = len(messages) - config.KEEP_LAST
    while cut < len(messages) and not isinstance(messages[cut], HumanMessage):
        cut += 1

    old = messages[:cut]
    if len(old) < 2:
        return {"messages": repair} if repair else {}

    # 3. COMPRESS: merge the old messages into the existing summary.
    existing = state.get("summary", "")
    prompt = _transcript(old)
    if existing:
        prompt = (
            f"Current summary of the conversation:\n{existing}\n\n"
            f"New conversation since then:\n{prompt}\n\n"
            "Write an updated summary. Keep every concrete fact: product names, "
            "ASINs, prices, ratings, decisions and user preferences."
        )
    else:
        prompt = (
            f"Conversation:\n{prompt}\n\n"
            "Summarize this conversation. Keep every concrete fact: product names, "
            "ASINs, prices, ratings, decisions and user preferences."
        )

    summary = llm.invoke([HumanMessage(content=prompt)]).content

    # Returning RemoveMessage objects tells the messages reducer to DELETE
    # those messages from state. This is the trick that shrinks the thread.
    # (repair removes are included so a healed dangling message also goes.)
    return {
        "summary": summary,
        "messages": repair + [RemoveMessage(id=m.id) for m in old],
    }


# ---------------------------------------------------------------------------
# 3. THE AGENT NODE  (the brain)
# ---------------------------------------------------------------------------
def agent_node(state: State):
    """One LLM call that decides what to do next.

    The model sees:
      - the system prompt (its persona and rules)
      - the running summary, if one exists (the compressed past)
      - the recent messages, verbatim

    Its response is either a final answer (plain text) or one or more
    tool calls. We do not decide that; the model does. That decision is
    routed by `tools_condition` in build_graph below.
    """
    market = oxylabs_client.get_marketplace()
    label = config.MARKETPLACES.get(market, {}).get("label", f"amazon.{market}")
    system = SYSTEM_PROMPT.format(domain=label)
    if state.get("summary"):
        system += f"\n\nSummary of the conversation so far:\n{state['summary']}"

    response = llm_with_tools.invoke([SystemMessage(content=system)] + state["messages"])
    return {"messages": [response]}


# ---------------------------------------------------------------------------
# 4. WIRING THE GRAPH
# ---------------------------------------------------------------------------
def build_graph(checkpointer):
    """Assemble the graph and attach the checkpointer.

    The checkpointer is passed in from outside (memory.py decides whether
    it is Postgres or SQLite). The graph code does not care: that is the
    whole point of the BaseCheckpointSaver interface.
    """
    builder = StateGraph(State)

    builder.add_node("summarize", summarize_node)
    builder.add_node("agent", agent_node)
    builder.add_node("tools", ToolNode(ALL_TOOLS))  # prebuilt executor for our tools

    builder.add_edge(START, "summarize")        # every turn: memory check first
    builder.add_edge("summarize", "agent")      # then let the brain think

    # Conditional edge: did the agent ask for a tool, or is it done?
    #   tool call present -> go to "tools"
    #   plain answer      -> go to END
    builder.add_conditional_edges("agent", tools_condition, {"tools": "tools", END: END})

    builder.add_edge("tools", "agent")          # tool result goes back to the brain

    # compile(checkpointer=...) is the line that gives the agent memory:
    # after every node runs, the full State is saved under the thread_id.
    return builder.compile(checkpointer=checkpointer)
