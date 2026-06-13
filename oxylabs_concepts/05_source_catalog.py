"""Concept 5: The source catalog — what else can Oxylabs scrape?

Every target is just a different "source" value in the same payload.
This script prints the catalog so the class sees the breadth, then
demonstrates ONE more source live: Amazon bestsellers.

Run:  uv run python oxylabs_concepts/05_source_catalog.py
"""
import os

import requests
from dotenv import load_dotenv

load_dotenv()

CATALOG = {
    "E-commerce": [
        ("amazon_search",      "keyword -> product listings"),
        ("amazon_product",     "ASIN -> full product page"),
        ("amazon_pricing",     "ASIN -> all competing offers"),
        ("amazon_bestsellers", "category -> bestseller list"),
        ("walmart_search / walmart_product", "Walmart"),
        ("flipkart_search / flipkart_product", "Flipkart (great for India)"),
        ("ebay_search / ebay_product", "eBay"),
        ("target / bestbuy / etsy / aliexpress ...", "40+ more stores"),
    ],
    "Search engines": [
        ("google_search",          "classic SERP, parsed"),
        ("google_shopping_search", "Google Shopping"),
        ("google_trends_explore",  "demand trends"),
        ("bing_search",            "Bing"),
    ],
    "AI answers (very 2026)": [
        ("chatgpt",    "what does ChatGPT answer for a prompt?"),
        ("perplexity", "what does Perplexity answer?"),
    ],
    "Other": [
        ("youtube_search / youtube_transcript", "YouTube data"),
        ("universal", "ANY url, raw HTML"),
    ],
}

for group, sources in CATALOG.items():
    print(f"\n{group}")
    print("-" * len(group))
    for name, what in sources:
        print(f"  {name:<38} {what}")

print("\n" + "=" * 70)
print("Live demo: amazon_bestsellers for 'electronics' on amazon.in")
print("=" * 70)

payload = {
    "source": "amazon_bestsellers",
    "domain": "in",
    "query": "electronics",
    "parse": True,
}
response = requests.post(
    "https://realtime.oxylabs.io/v1/queries",
    auth=(os.environ["OXYLABS_USERNAME"], os.environ["OXYLABS_PASSWORD"]),
    json=payload,
    timeout=90,
)
response.raise_for_status()
content = response.json()["results"][0]["content"]
items = content.get("results", [])

for item in items[:8]:
    print(
        f"  #{item.get('pos','?'):<3} "
        f"{item.get('price') or '-':>8} "
        f"★{item.get('rating') or '-'}  "
        f"{(item.get('title') or '')[:55]}"
    )
