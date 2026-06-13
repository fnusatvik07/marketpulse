"""Concept 4: Scraping ANY website with the universal source.

Amazon, Walmart, Google etc. have dedicated sources with parsers.
For everything else there is source="universal": give it a URL, get
the page back, scraped through Oxylabs' proxy network. No parser, so
you receive HTML and extract what you need yourself.

Run:  uv run python oxylabs_concepts/04_any_website.py
"""
import os
import re

import requests
from dotenv import load_dotenv

load_dotenv()

payload = {
    "source": "universal",
    "url": "https://books.toscrape.com/",   # a site built for scraping practice
}

response = requests.post(
    "https://realtime.oxylabs.io/v1/queries",
    auth=(os.environ["OXYLABS_USERNAME"], os.environ["OXYLABS_PASSWORD"]),
    json=payload,
    timeout=90,
)
response.raise_for_status()
html = response.json()["results"][0]["content"]

print("Fetched", len(html), "characters of HTML through Oxylabs.\n")

# quick-and-dirty extraction, just to show the HTML is real
titles = re.findall(r'title="([^"]+)"', html)
prices = re.findall(r'£([\d.]+)', html)

print("First books on the page:")
for title, price in list(zip(titles[3:], prices))[:8]:
    print(f"  £{price:<7} {title[:60]}")

print("\nFor real HTML parsing you would use BeautifulSoup here.")
print("Dedicated sources (amazon_*, google_*, walmart_*) skip that step entirely.")
