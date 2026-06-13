"""Concept 3: One product, full depth.

The amazon_product source takes a 10-character ASIN and returns
everything on the product page: pricing, stock, rating distribution,
sales rank, images, the works.

Run:  uv run python oxylabs_concepts/03_amazon_product.py
      uv run python oxylabs_concepts/03_amazon_product.py B0FC2YFSN4
"""
import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

ASIN = sys.argv[1] if len(sys.argv) > 1 else "B0FC2YFSN4"   # boAt Airdopes 219

payload = {
    "source": "amazon_product",
    "domain": "in",
    "query": ASIN,
    "parse": True,
    # autoselect_variant gives accurate price/buybox for products
    # that have variations (colours, sizes)
    "context": [{"key": "autoselect_variant", "value": True}],
}

response = requests.post(
    "https://realtime.oxylabs.io/v1/queries",
    auth=(os.environ["OXYLABS_USERNAME"], os.environ["OXYLABS_PASSWORD"]),
    json=payload,
    timeout=90,
)
response.raise_for_status()
c = response.json()["results"][0]["content"]

print("title:        ", (c.get("title") or "")[:80])
print("brand:        ", c.get("brand") or c.get("manufacturer"))
print("price:        ", c.get("price"), c.get("currency"))
print("was-price:    ", c.get("price_initial") or "-")
print("stock:        ", c.get("stock"))
print("rating:       ", c.get("rating"), f"({c.get('reviews_count')} reviews)")

if c.get("sales_rank"):
    first = c["sales_rank"][0]
    cat = first["ladder"][0]["name"] if first.get("ladder") else "?"
    print("sales rank:   ", f"#{first.get('rank')} in {cat}")

print("\nimage URLs (the agent's download tool fetches these):")
for url in (c.get("images") or [])[:4]:
    print("  ", url)

print("\nrating distribution:")
for row in c.get("rating_stars_distribution") or []:
    print(f"   {row.get('rating')} star: {row.get('percentage')}%")
