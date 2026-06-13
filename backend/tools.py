"""The agent's tools: what the LLM is ALLOWED to do in the real world.

Each function below becomes a tool the moment we decorate it with @tool.
Three things to point out when reading them:

  1. The DOCSTRING is not for humans. It is sent to the LLM, and it is
     how the model decides which tool to pick. Write docstrings like
     you are explaining the tool to a new intern.

  2. Every tool returns a compact JSON STRING, never a raw scrape.
     A full Oxylabs product response is thousands of tokens; we slim it
     to the dozen fields the agent actually needs. Smaller tool output
     means cheaper, faster, sharper agents.

  3. Tools are plain Python. Scraping, file downloads, anything. The
     agent does not know how they work inside, only their signatures.
"""
import functools
import json
import logging
import re
from pathlib import Path

import requests
from langchain_core.tools import tool

from . import config, oxylabs_client

logger = logging.getLogger(__name__)


def safe(fn):
    """A tool should RETURN an error, never raise it.

    If a tool raises, the graph crashes mid-turn and can leave the thread in a
    broken state (an assistant tool-call with no tool result, which the LLM API
    then rejects on every later turn). Catching here means the agent always
    gets a result it can reason about and recover from.
    """
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001 - deliberately broad
            logger.exception("tool %s failed", fn.__name__)
            return json.dumps({"error": f"{type(exc).__name__}: {exc}"})
    return wrapper


def _organic(content: dict) -> list:
    """Pull the organic search results out of an amazon_search response.

    Oxylabs returns `content["results"]` as either a dict
    ({"organic": [...], "paid": [...]}) or, on some pages, a plain list.
    This helper handles both so the tools never crash on the shape.
    """
    results = content.get("results")
    if isinstance(results, dict):
        return results.get("organic", []) or []
    if isinstance(results, list):
        return results
    return []


def _asin_from(text: str) -> str:
    """Accept a raw ASIN or a full Amazon URL and return the 10-char ASIN.

    Users often paste the whole product URL; the agent may pass it through.
    Patterns like /dp/B07G11R5LC or ?ASIN=B07G11R5LC are extracted here.
    """
    text = (text or "").strip()
    if re.fullmatch(r"[A-Z0-9]{10}", text):
        return text
    for pat in (r"/dp/([A-Z0-9]{10})", r"/gp/product/([A-Z0-9]{10})",
                r"/product/([A-Z0-9]{10})", r"[?&]ASIN=([A-Z0-9]{10})",
                r"\b([A-Z0-9]{10})\b"):
        m = re.search(pat, text)
        if m:
            return m.group(1)
    return text


def _slim_search_item(item: dict) -> dict:
    return {
        "asin": item.get("asin"),
        "title": (item.get("title") or "")[:90],
        "price": item.get("price"),
        "currency": item.get("currency"),
        "rating": item.get("rating"),
        "reviews_count": item.get("reviews_count"),
        "sales_volume": item.get("sales_volume"),
        "best_seller": item.get("best_seller"),
        "image": item.get("url_image"),
    }


@tool
@safe
def search_products(query: str, max_results: int = 8) -> str:
    """Search Amazon for products by keywords. Returns a JSON list of
    products with ASIN, title, price, rating and review count.
    Use this first when the user mentions a product by name."""
    content = oxylabs_client.scrape("amazon_search", query)
    organic = _organic(content)
    items = [_slim_search_item(i) for i in organic if i.get("asin")][:max_results]
    return json.dumps({"query": query, "products": items})


def _review_summary(c: dict) -> dict:
    """Rating, star distribution and a few recent review snippets — the
    data needed to compare products on their reviews."""
    dist = {}
    for row in c.get("rating_stars_distribution") or []:
        if row.get("rating") is not None:
            dist[f"{row['rating']}_star"] = row.get("percentage")
    snippets = []
    for rev in (c.get("reviews") or [])[:4]:
        snippets.append({
            "rating": rev.get("rating"),
            "title": (rev.get("title") or "")[:80],
            "text": (rev.get("content") or "")[:200],
        })
    return {
        "rating": c.get("rating"),
        "reviews_count": c.get("reviews_count"),
        "star_distribution": dist or None,
        "recent_reviews": snippets or None,
    }


@tool
@safe
def get_product_details(asin: str) -> str:
    """Get full details for one Amazon product. Accepts a 10-character ASIN
    or a full Amazon product URL. Returns price, original price, rating,
    review summary with recent review snippets, stock, key features,
    sales rank and image URLs."""
    asin = _asin_from(asin)
    c = oxylabs_client.scrape("amazon_product", asin, autoselect_variant=True)
    rank = None
    if isinstance(c.get("sales_rank"), list) and c["sales_rank"]:
        first = c["sales_rank"][0]
        ladder = first.get("ladder", []) if isinstance(first, dict) else []
        rank = {
            "rank": first.get("rank") if isinstance(first, dict) else None,
            "category": ladder[0]["name"] if ladder else None,
        }
    details = {
        "asin": c.get("asin"),
        "title": (c.get("title") or "")[:120],
        "brand": c.get("brand") or c.get("manufacturer"),
        "price": c.get("price"),
        "price_strikethrough": c.get("price_initial") or None,
        "currency": c.get("currency"),
        "stock": c.get("stock"),
        "features": (c.get("bullet_points") or "")[:500],
        "sales_rank": rank,
        "images": (c.get("images") or [])[:6],
        "reviews": _review_summary(c),
    }
    return json.dumps({"product": details})


@tool
@safe
def find_competitors(asin: str, max_competitors: int = 5) -> str:
    """Find competing products for a given ASIN. Scrapes the product,
    searches Amazon with a cleaned version of its title, and returns
    rival products with their prices for comparison."""
    # This tool is two scrapes chained inside ONE tool:
    #   product page -> clean its title -> search that title -> filter
    # You could also leave this to the agent (it could call
    # get_product_details then search_products itself), but a dedicated
    # tool is faster, cheaper and more predictable. Where to draw the
    # line between "one smart tool" vs "let the agent compose small
    # tools" is a real design decision in agent engineering.
    asin = _asin_from(asin)
    c = oxylabs_client.scrape("amazon_product", asin, autoselect_variant=True)
    title = c.get("title") or ""
    brand = (c.get("brand") or c.get("manufacturer") or "").strip()

    # Some product pages return a generic meta title like
    # "Amazon.com: Conquest 41MM Quartz Watch : Clothing, Shoes & Jewelry".
    # Strip that wrapper down to the part between the colons.
    short = re.sub(r"^Amazon\.[a-z.]+:\s*", "", title)
    short = short.split(" : ")[0]            # drop trailing " : Category" tail
    short = short.split(",")[0]              # drop spec list after first comma
    if brand:
        short = re.sub(re.escape(brand), "", short, flags=re.IGNORECASE)
    short = re.sub(r"\(.*?\)", "", short).strip()
    # Fall back to a brand search if cleaning left us with nothing useful.
    if len(short) < 3:
        short = brand or title[:40]

    content = oxylabs_client.scrape("amazon_search", short)
    organic = _organic(content)

    competitors = []
    seen = {asin}
    for item in organic:
        item_asin = item.get("asin")
        if not item_asin or item_asin in seen:
            continue
        seen.add(item_asin)
        slim = _slim_search_item(item)
        if slim["price"] and c.get("price"):
            slim["price_diff_vs_main"] = round(slim["price"] - c["price"], 2)
        competitors.append(slim)
        if len(competitors) >= max_competitors:
            break

    main = {"asin": asin, "title": title[:90], "price": c.get("price")}
    return json.dumps(
        {"main_product": main, "search_used": short, "competitors": competitors}
    )


@tool
@safe
def download_product_images(asin: str, max_images: int = 4) -> str:
    """Download the product images for an ASIN to local storage so the
    user can view them in the app. Returns the local image paths.
    Use when the user asks to see, save or download product images."""
    asin = _asin_from(asin)
    c = oxylabs_client.scrape("amazon_product", asin, autoselect_variant=True)
    urls = (c.get("images") or [])[:max_images]

    target = config.DOWNLOADS_DIR / asin
    target.mkdir(parents=True, exist_ok=True)

    saved = []
    for i, url in enumerate(urls):
        ext = Path(url.split("?")[0]).suffix or ".jpg"
        filename = f"image_{i + 1}{ext}"
        path = target / filename
        if not path.exists():
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            path.write_bytes(r.content)
        saved.append(f"/downloads/{asin}/{filename}")

    return json.dumps(
        {"asin": asin, "title": (c.get("title") or "")[:90], "downloaded": saved}
    )


ALL_TOOLS = [search_products, get_product_details, find_competitors, download_product_images]
