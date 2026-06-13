"""Concept 1: Your first Oxylabs request.

The entire Web Scraper API is ONE endpoint:

    POST https://realtime.oxylabs.io/v1/queries

You send a small JSON payload saying WHAT to scrape (the "source") and
the query. Oxylabs handles proxies, anti-bot bypassing and parsing.
You get structured JSON back. That is the whole product.

Run:  uv run python oxylabs_concepts/01_first_request.py
"""
import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()

USERNAME = os.environ["OXYLABS_USERNAME"]
PASSWORD = os.environ["OXYLABS_PASSWORD"]

# The payload: scrape an Amazon search page for "wireless earbuds"
# and parse it into structured JSON (parse=True is the magic flag).
payload = {
    "source": "amazon_search",
    "domain": "in",                 # amazon.in
    "query": "wireless earbuds",
    "parse": True,
}

print("Sending one POST request to Oxylabs...")
response = requests.post(
    "https://realtime.oxylabs.io/v1/queries",
    auth=(USERNAME, PASSWORD),      # plain HTTP basic auth
    json=payload,
    timeout=90,
)
response.raise_for_status()

data = response.json()

# The response shape is always: {"results": [{"content": <parsed page>}]}
content = data["results"][0]["content"]

print("\nStatus:", response.status_code)
print("Top-level keys in the parsed content:")
for key in content.keys():
    print("  -", key)

print("\nTotal results Amazon reported:", content.get("total_results_count"))
print("\nFirst organic result, raw:")
first = content["results"]["organic"][0]
print(json.dumps(first, indent=2)[:600])
