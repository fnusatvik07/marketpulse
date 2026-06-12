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
import json
import re
from pathlib import Path

import requests
from langchain_core.tools import tool

from . import config, oxylabs_client


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
def search_products(query: str, max_results: int = 8) -> str:
    """Search Amazon for products by keywords. Returns a JSON list of
    products with ASIN, title, price, rating and review count.
    Use this first when the user mentions a product by name."""
    content = oxylabs_client.scrape("amazon_search", query)
    organic = content.get("results", {}).get("organic", [])
    items = [_slim_search_item(i) for i in organic if i.get("asin")][:max_results]
    return json.dumps({"query": query, "products": items})


@tool
def get_product_details(asin: str) -> str:
    """Get full details for one Amazon product by its 10-character ASIN:
    price, original price, rating, reviews, stock, key features,
    sales rank and image URLs."""
    c = oxylabs_client.scrape("amazon_product", asin, autoselect_variant=True)
    rank = None
    if c.get("sales_rank"):
        first = c["sales_rank"][0]
        ladder = first.get("ladder", [])
        rank = {
            "rank": first.get("rank"),
            "category": ladder[0]["name"] if ladder else None,
        }
    details = {
        "asin": c.get("asin"),
        "title": (c.get("title") or "")[:120],
        "brand": c.get("brand") or c.get("manufacturer"),
        "price": c.get("price"),
        "price_strikethrough": c.get("price_initial") or None,
        "currency": c.get("currency"),
        "rating": c.get("rating"),
        "reviews_count": c.get("reviews_count"),
        "stock": c.get("stock"),
        "features": (c.get("bullet_points") or "")[:500],
        "sales_rank": rank,
        "images": (c.get("images") or [])[:6],
    }
    return json.dumps({"product": details})


@tool
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
    c = oxylabs_client.scrape("amazon_product", asin, autoselect_variant=True)
    title = c.get("title") or ""
    brand = (c.get("brand") or c.get("manufacturer") or "").strip()

    # Clean the title: drop the brand name and everything after the first
    # comma, so "boAt Airdopes 219, 4Mics ENx..." becomes "Airdopes 219".
    short = title.split(",")[0]
    if brand:
        short = re.sub(re.escape(brand), "", short, flags=re.IGNORECASE)
    short = re.sub(r"\(.*?\)", "", short).strip() or title[:40]

    content = oxylabs_client.scrape("amazon_search", short)
    organic = content.get("results", {}).get("organic", [])

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
def download_product_images(asin: str, max_images: int = 4) -> str:
    """Download the product images for an ASIN to local storage so the
    user can view them in the app. Returns the local image paths.
    Use when the user asks to see, save or download product images."""
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
