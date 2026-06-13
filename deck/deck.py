"""MarketPulse project deck — 6 slides, paper-light brand."""
import os
os.environ.setdefault("CINEDECK_WORDMARK", "MarketPulse")
os.environ.setdefault("CINEDECK_ICONS", os.path.expanduser("~/.claude/skills/cinematic-deck/scripts/icons"))

import engine as E
from engine import *

SS = "../docs/screenshots"
LG = "icons_local/langgraph.svg"
AMZ = "icons_local/amazon.svg"
OXY_PURPLE = "#4A2EE2"


def framed_image(path, x, y, w, h, r=12):
    """Screenshot in a white card frame with soft shadow."""
    uri = data_uri(path)
    return (
        f'<g filter="url(#ds)">{rrect(x-10, y-10, w+20, h+20, r+4, fill="#FFFFFF", stroke=LINE, sw=1.2)}</g>'
        f'<clipPath id="f{int(x)}{int(y)}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}"/></clipPath>'
        f'<image href="{uri}" x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid slice" clip-path="url(#f{int(x)}{int(y)})"/>'
    )


def node(x, y, w, h, title, sub, accent, icon_key=None, big=False):
    """Light card node for diagrams: accent top bar, optional logo badge, labels."""
    b = [f'<g filter="url(#ds)">{rrect(x, y, w, h, 12, fill="url(#cardg)", stroke=LINE, sw=1.2)}</g>',
         f'<rect x="{x}" y="{y}" width="{w}" height="5" rx="2.5" fill="{accent}"/>']
    tx = x + w / 2
    iy = y + (34 if big else 30)
    if icon_key:
        b.append(badge(tx, iy + 6, 44 if big else 38, icon_key))
        ty = iy + (44 if big else 38)
    else:
        ty = y + (40 if big else 34)
    b.append(txt(tx, ty + 16, title, 19 if big else 16.5, WHITE, FAM_BODY, 700, "middle"))
    if sub:
        b.append(txt(tx, ty + 36, sub, 12.5, CAP, FAM_BODY, 400, "middle"))
    return "\n".join(b)


def msg_rows(x, y, w, rows):
    """Tiny message-list rows for the summarization visual. rows=[(label,kind)]"""
    b = []
    for i, (label, kind) in enumerate(rows):
        ry = y + i * 30
        fill, stroke, tcol = ("#FBEAE8", "#D8A49C", RED) if kind == "old" else ("#E9F3EC", "#A9CDB8", BLUED)
        b.append(rrect(x, ry, w, 24, 6, fill=fill, stroke=stroke, sw=1))
        if label:
            b.append(txt(x + w / 2, ry + 16.5, label, 12.5, tcol, FAM_BODY, 600, "middle"))
    return "\n".join(b)


# ============================================================ slide 1 · title
def s_title(p):
    b = [f'<rect width="{W}" height="{H}" fill="url(#bg)"/>',
         f'<rect width="{W}" height="{H}" fill="url(#sun)"/>']
    lx = 84
    pl, _ = pill(lx, 92, "LANGGRAPH · SHORT-TERM MEMORY · ENTERPRISE PROJECT", stroke=BLUE, text_fill=BLUED)
    b.append(pl)
    b.append(rich(lx, 248, [
        {"t": "Market", "fill": WHITE, "size": 96, "family": FAM_DISPLAY, "weight": 900},
        {"t": "Pulse", "fill": BLUE, "size": 96, "family": FAM_DISPLAY, "weight": 900},
    ], anchor="start"))
    b.append(f'<rect x="{lx}" y="282" width="130" height="5" fill="{GOLD}"/>')
    for i, ln in enumerate(wrap("An AI market analyst that scrapes Amazon live — and never forgets a conversation.", F_MED, 24, 470)):
        b.append(txt(lx, 340 + i * 34, ln, 24, CREAM, FAM_BODY, 500))
    feats = ["Live scraping via Oxylabs", "Postgres checkpointer memory", "Hand-built summarization node"]
    for i, ftext in enumerate(feats):
        fy = 460 + i * 38
        b.append(f'<circle cx="{lx+7}" cy="{fy-6}" r="4.5" fill="{BLUE}"/>')
        b.append(txt(lx + 24, fy, ftext, 18.5, CAP, FAM_BODY, 500))
    b.append(txt(lx, 606, "github.com/fnusatvik07/marketpulse", 15, MUTE, FAM_MONO, 400))
    b.append(framed_image(f"{SS}/main.png", 650, 168, 548, 335))
    return page("\n".join(b), bg=None, glow=False, topic="The project", page_no=p)


# ============================================================ slide 2 · why / use cases
def s_why(p):
    b = []
    content_header(b, "WHY IT EXISTS", "Market research is manual, slow, and stale")
    lx, lw = 84, 380
    paras = [
        "Sellers check rival prices by hand, screenshot listings, and paste reviews into spreadsheets.",
        "By the time the sheet is ready, the market has moved: prices changed, a new rival launched.",
        "MarketPulse turns all of that into one conversation backed by live scraped data.",
    ]
    yy = 232
    for para in paras:
        for ln in wrap(para, F_REG, 19.5, lw):
            b.append(txt(lx, yy, ln, 19.5, CAP, FAM_BODY, 400)); yy += 28
        yy += 16
    cases = [
        ("Launch pricing", "Know every rival's price before you set yours"),
        ("Competitor tracking", "Live watch on rival ASINs, ratings, discounts"),
        ("Voice of customer", "What buyers love and hate, mined from reviews"),
        ("Listing intelligence", "Images, bullets and sales ranks on demand"),
    ]
    cw, chh, gap = 330, 122, 22
    x0, y0 = 520, 212
    for i, (t, s) in enumerate(cases):
        r, c = divmod(i, 2)
        x, y = x0 + c * (cw + gap), y0 + r * (chh + gap)
        b.append(f'<g filter="url(#ds)">{rrect(x, y, cw, chh, 12, fill="url(#cardg)", stroke=LINE, sw=1.2)}</g>')
        b.append(f'<rect x="{x}" y="{y}" width="5" height="{chh}" rx="2.5" fill="{BLUE if i%2==0 else GOLD}"/>')
        b.append(txt(x + 26, y + 44, t, 21, WHITE, FAM_DISPLAY, 600))
        for j, ln in enumerate(wrap(s, F_REG, 15.5, cw - 50)):
            b.append(txt(x + 26, y + 74 + j * 22, ln, 15.5, CAP, FAM_BODY, 400))
    yy = y0 + 2 * (chh + gap) + 40
    b.append(txt(x0, yy, "WHO USES IT", 13, GOLD, FAM_BODY, 700, spacing=2.5))
    px = x0
    for who in ["D2C sellers", "Marketplace agencies", "Category managers"]:
        plw, w_ = pill(px, yy + 16, who, stroke=BORDER1, text_fill=CREAM, size=14)
        b.append(plw); px += w_ + 14
    return page("\n".join(b), topic="The problem", page_no=p)


# ============================================================ slide 3 · the experience
def s_experience(p):
    b = []
    b.append(eyebrow(84, 120, "THE EXPERIENCE"))
    yy = 178
    for ln in ["Ask. It scrapes,", "compares, recommends."]:
        b.append(txt(84, yy, ln, 44, WHITE, FAM_DISPLAY, 600, spacing=0.5)); yy += 52
    yy += 26
    paras = [
        "Type a question — the agent scrapes amazon.in live through Oxylabs and answers like an analyst, with tables and sources.",
        "A market dashboard builds itself: price ladder, rating scatter, Best Value and Top Rated picks.",
        "Ask for product images and it downloads them straight into the app.",
        "Every turn is one POST /chat with a thread_id. The UI is optional — the brain lives in the backend.",
    ]
    for para in paras:
        for ln in wrap(para, F_REG, 19, 440):
            b.append(txt(84, yy, ln, 19, CAP, FAM_BODY, 400)); yy += 27
        yy += 15
    b.append(framed_image(f"{SS}/query.png", 600, 158, 596, 364))
    b.append(txt(898, 568, "Live answer with product cards, picks and the analytics board", 14.5, MUTE, FAM_BODY, 500, "middle"))
    return page("\n".join(b), topic="The experience", page_no=p)


# ============================================================ slide 4 · architecture
def s_architecture(p):
    b = []
    content_header(b, "UNDER THE HOOD", "The backend in one picture")
    fastapi = E.ensure_icon("fastapi"); openai_l = E.ensure_icon("openai"); pg = E.ensure_icon("postgresql")

    b.append(node(84, 300, 130, 96, "User", "chat or CLI", GOLD))
    b.append(node(282, 300, 170, 96, "FastAPI", "the HTTP door", "#009688", icon_key=fastapi))
    b.append(node(520, 282, 210, 132, "LangGraph agent", "decides · acts · loops", "#1C3C3C", icon_key=LG, big=True))
    b.append(node(820, 168, 180, 96, "OpenAI", "the reasoning", "#10A37F", icon_key=openai_l))
    b.append(node(820, 300, 180, 96, "Oxylabs", "scraping API", OXY_PURPLE))
    b.append(node(1064, 300, 140, 96, "Amazon", "live data", "#FF9900", icon_key=AMZ))
    b.append(node(820, 432, 180, 96, "Postgres", "the memory", "#4169E1", icon_key=pg))

    def lbl(x, y, s):
        return txt(x, y, s, 13.5, MUTE, FAM_BODY, 600, "middle")
    b.append(arrow(216, 348, 280, BORDER2))
    b.append(arrow(454, 348, 518, BORDER2))
    b.append(line(730, 322, 818, 232, SKYBLUE, 2)); b.append(f'<path d="M810 228 L822 230 L814 240 Z" fill="{SKYBLUE}"/>')
    b.append(txt(748, 254, "thinks", 13.5, MUTE, FAM_BODY, 600, "end"))
    b.append(arrow(732, 348, 818, BLUE)); b.append(lbl(775, 338, "tool calls"))
    b.append(arrow(1002, 348, 1062, "#FF9900")); b.append(lbl(1032, 338, "scrapes"))
    b.append(line(730, 380, 818, 470, "#4169E1", 2)); b.append(f'<path d="M810 472 L822 470 L816 460 Z" fill="#4169E1"/>')
    b.append(txt(744, 460, "checkpoints", 13.5, MUTE, FAM_BODY, 600, "end"))
    b.append(txt(84, 478, "thread_id", 15, BLUED, FAM_MONO, 600))
    for i, ln in enumerate(wrap("One id in the request config decides which conversation the agent wakes up in.", F_REG, 15.5, 350)):
        b.append(txt(84, 502 + i * 22, ln, 15.5, CAP, FAM_BODY, 400))
    b.append(txt(W/2, H-86, "FastAPI is just the door. All intelligence — and all memory — lives inside the LangGraph graph.", 19, CAP, FAM_BODY, 500, "middle"))
    return page("\n".join(b), topic="Architecture", page_no=p)


# ============================================================ slide 5 · memory
def s_memory(p):
    b = []
    content_header(b, "SHORT-TERM MEMORY", "How LangGraph remembers")
    pg = E.ensure_icon("postgresql")

    # left: the graph, vertical
    gx = 110
    steps = ["START", "summarize", "agent", "END"]
    accents = ["#1C3C3C", GOLD, "#10A37F", "#1C3C3C"]
    sy = 214
    for i, label in enumerate(steps):
        y = sy + i * 88
        dark = label in ("START", "END")
        b.append(f'<g filter="url(#ds)">{rrect(gx, y, 170, 54, 10, fill=("#1C3C3C" if dark else "url(#cardg)"), stroke=("#1C3C3C" if dark else accents[i]), sw=1.4)}</g>')
        b.append(txt(gx + 85, y + 34, label, 17, ("#F7F4EC" if dark else WHITE), FAM_BODY, 700, "middle"))
        if i < 3:
            b.append(line(gx + 85, y + 56, gx + 85, y + 84, BORDER2, 2))
            b.append(f'<path d="M{gx+79} {y+78} L{gx+85} {y+86} L{gx+91} {y+78} Z" fill="{BORDER2}"/>')
    ay = sy + 2 * 88
    b.append(f'<g filter="url(#ds)">{rrect(gx + 240, ay, 150, 54, 10, fill="url(#cardg)", stroke="#4169E1", sw=1.4)}</g>')
    b.append(txt(gx + 315, ay + 34, "tools", 17, WHITE, FAM_BODY, 700, "middle"))
    b.append(line(gx + 172, ay + 16, gx + 238, ay + 16, "#10A37F", 2))
    b.append(f'<path d="M{gx+232} {ay+10} L{gx+240} {ay+16} L{gx+232} {ay+22} Z" fill="#10A37F"/>')
    b.append(line(gx + 238, ay + 38, gx + 172, ay + 38, "#4169E1", 2))
    b.append(f'<path d="M{gx+178} {ay+32} L{gx+170} {ay+38} L{gx+178} {ay+44} Z" fill="#4169E1"/>')
    b.append(txt(gx + 315, ay + 76, "loops until done", 13, MUTE, FAM_BODY, 500, "middle"))

    # right: postgres checkpoints panel
    px, py, pw, ph = 560, 206, 640, 312
    b.append(f'<g filter="url(#ds)">{rrect(px, py, pw, ph, 16, fill="url(#cardg)", stroke=LINE, sw=1.2)}</g>')
    b.append(badge(px + 44, py + 42, 44, pg))
    b.append(txt(px + 78, py + 50, "checkpoints table — the agent's entire memory", 19, WHITE, FAM_BODY, 700))
    rows = [("thread_id = mp-001  ·  checkpoint #1  ·  full graph state", SURF1),
            ("thread_id = mp-001  ·  checkpoint #2  ·  full graph state", SURF1),
            ("thread_id = mp-001  ·  checkpoint #3  ·  ...", SURF1),
            ("thread_id = mp-002  ·  another user, fully isolated", "#F1EDE2")]
    for i, (rtext, fill) in enumerate(rows):
        ry = py + 86 + i * 44
        b.append(rrect(px + 32, ry, pw - 64, 34, 8, fill=fill, stroke=LINE, sw=1))
        b.append(txt(px + 52, ry + 22.5, rtext, 14.5, CREAM, FAM_MONO, 500))
    b.append(txt(px + 32, py + ph - 24, "Kill the server. Restart it. The thread continues exactly where it stopped.", 17, BLUED, FAM_BODY, 700))
    b.append(txt(W/2, H-86, "A checkpoint = the full graph state, saved after every step, keyed by thread_id. Swap Postgres for Redis or MongoDB in one line.", 18, CAP, FAM_BODY, 500, "middle"))
    return page("\n".join(b), topic="Checkpointers", page_no=p)


# ============================================================ slide 6 · summarization + close
def s_summarize(p):
    b = []
    content_header(b, "COST CONTROL", "The summarization node keeps long chats cheap")
    openai_l = E.ensure_icon("openai")

    # before panel
    bx, by, bw = 96, 200, 300
    b.append(f'<g filter="url(#ds)">{rrect(bx, by, bw, 296, 14, fill="url(#cardg)", stroke=LINE, sw=1.2)}</g>')
    b.append(txt(bx + 24, by + 36, "Before · 14 messages", 17, WHITE, FAM_BODY, 700))
    b.append(msg_rows(bx + 24, by + 56, bw - 48, [
        ("messages 1 – 10  (old)", "old"), ("", "old"), ("", "old"),
        ("messages 11 – 13  (recent)", "keep"), ("new user question", "keep"),
    ]))
    b.append(txt(bx + 24, by + 240, "every turn re-sends all of it,", 13.5, RED, FAM_BODY, 600))
    b.append(txt(bx + 24, by + 260, "cost grows forever", 13.5, RED, FAM_BODY, 600))

    # middle: LLM folds
    mx = 470
    b.append(arrow(bx + bw + 14, 348, mx - 12, GOLD))
    b.append(f'<g filter="url(#ds)">{rrect(mx, 296, 190, 104, 14, fill="url(#cardg)", stroke="#10A37F", sw=1.4)}</g>')
    b.append(badge(mx + 95, 332, 40, openai_l))
    b.append(txt(mx + 95, 382, "LLM folds the old", 14.5, WHITE, FAM_BODY, 700, "middle"))
    b.append(arrow(mx + 202, 348, 742, GOLD))

    # after panel
    ax, ay, aw = 754, 200, 300
    b.append(f'<g filter="url(#ds)">{rrect(ax, ay, aw, 296, 14, fill="url(#cardg)", stroke="#1C6B46", sw=1.4)}</g>')
    b.append(txt(ax + 24, ay + 36, "After · 4 messages", 17, WHITE, FAM_BODY, 700))
    b.append(rrect(ax + 24, ay + 54, aw - 48, 56, 8, fill="#FCF3DD", stroke=GOLD, sw=1.2))
    b.append(txt(ax + 24 + (aw - 48) / 2, ay + 77, "running summary", 13.5, GOLD, FAM_BODY, 700, "middle"))
    b.append(txt(ax + 24 + (aw - 48) / 2, ay + 96, "every fact survives here", 12, CAP, FAM_BODY, 500, "middle"))
    b.append(msg_rows(ax + 24, ay + 124, aw - 48, [
        ("messages 11 – 13  (recent)", "keep"), ("new user question", "keep"),
    ]))
    b.append(txt(ax + 24, ay + 212, "old messages deleted with", 13.5, CAP, FAM_BODY, 500))
    b.append(txt(ax + 24, ay + 232, "RemoveMessage(id=...)", 14, RED, FAM_MONO, 600))
    b.append(txt(ax + 24, ay + 262, "context cost stays flat, forever", 14, BLUED, FAM_BODY, 700))

    # closing strip: stack + repo
    sy = 574
    b.append(line(96, sy - 26, W - 96, sy - 26, LINE, 1, 0.8))
    chips = ["python", "fastapi", None, "openai", "postgresql", "react", "docker-icon"]
    cx = 120
    for key in chips:
        k = E.ensure_icon(key) if key else LG
        if k:
            b.append(logo_chip(cx, sy + 10, 40, k)); cx += 58
    b.append(txt(W - 96, sy + 16, "github.com/fnusatvik07/marketpulse", 16, BLUED, FAM_MONO, 600, "end"))
    return page("\n".join(b), topic="Summarization", page_no=p)


SLIDES = [
    ("01_title", s_title),
    ("02_why", s_why),
    ("03_experience", s_experience),
    ("04_architecture", s_architecture),
    ("05_memory", s_memory),
    ("06_summarization", s_summarize),
]

if __name__ == "__main__":
    pngs = []
    for i, (name, fn) in enumerate(SLIDES):
        pngs.append((name, render(fn(i + 1), name), False))
        print("rendered", name)
    build_pptx(pngs, os.path.join(OUT, "MarketPulse_Deck.pptx"))
    contact_sheet([p_ for _, p_, _ in pngs], os.path.join(OUT, "_sheet.png"), cols=3)
    print("done")
