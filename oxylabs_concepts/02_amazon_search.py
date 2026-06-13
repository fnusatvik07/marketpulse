"""Concept 2: Amazon search, cleaned up.

Same request as concept 1, but now we slim the response down to the
fields an application actually needs. Compare the sizes at the end:
this is why you never feed raw scrapes to an LLM.

Run:  uv run python oxylabs_concepts/02_amazon_search.py
"""
import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()

payload = {
    "source": "amazon_search",
    "domain": "in",
    "query": "smart watch under 3000",
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

# organic = real results; Amazon also returns paid (sponsored) ones
organic = content["results"]["organic"]

print(f"{'ASIN':<12} {'PRICE':>8} {'RATING':>7} {'REVIEWS':>9}  TITLE")
print("-" * 95)
for item in organic[:10]:
    print(
        f"{item.get('asin',''):<12} "
        f"{item.get('price') or '-':>8} "
        f"{item.get('rating') or '-':>7} "
        f"{item.get('reviews_count') or '-':>9}  "
        f"{(item.get('title') or '')[:48]}"
    )

raw_size = len(json.dumps(content))
slim = [
    {k: item.get(k) for k in ("asin", "title", "price", "rating", "reviews_count")}
    for item in organic[:10]
]
slim_size = len(json.dumps(slim))

print("\nraw parsed page:", raw_size, "characters")
print("slimmed for the agent:", slim_size, "characters")
print(f"that is {raw_size // max(slim_size,1)}x smaller. LLM context is money.")
