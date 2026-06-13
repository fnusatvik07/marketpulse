"""Thin client for the Oxylabs Web Scraper API.

One function, `scrape(source, query)`, covers every Amazon source.
If credentials are missing (or OXYLABS_MOCK=true) it serves saved
fixture responses so the whole app works offline in a classroom.
"""
import contextvars
import json
import logging
from pathlib import Path

import requests

from . import config

logger = logging.getLogger(__name__)

FIXTURES_DIR = Path(__file__).parent / "fixtures"

# In-process cache so repeated questions in one session do not
# burn scraping credits for the same page.
_cache: dict = {}

# The marketplace for the CURRENT request. A context variable rather than a
# global so concurrent API requests (one user on amazon.in, another on
# amazon.com) never clobber each other. Set per turn in api.py / cli.py.
_active_domain: contextvars.ContextVar[str] = contextvars.ContextVar(
    "active_domain", default=config.AMAZON_DOMAIN
)


def set_marketplace(domain: str) -> None:
    """Choose the marketplace for subsequent scrapes in this context."""
    if domain in config.MARKETPLACES:
        _active_domain.set(domain)


def get_marketplace() -> str:
    """The marketplace currently in effect."""
    return _active_domain.get()


def _load_fixture(source: str) -> dict:
    name = "search_raw.json" if source == "amazon_search" else "product_raw.json"
    with open(FIXTURES_DIR / name) as f:
        data = json.load(f)
    return data["results"][0]["content"]


def scrape(source: str, query: str, domain: str | None = None, **context) -> dict:
    """Run one Oxylabs scraping job and return the parsed `content` dict.

    source: amazon_search | amazon_product | amazon_pricing | amazon_bestsellers
    query:  search keywords or a 10-character ASIN, depending on source
    """
    domain = domain or _active_domain.get()
    cache_key = (source, query, domain)
    if cache_key in _cache:
        logger.info("cache hit for %s %s", source, query)
        return _cache[cache_key]

    if config.OXYLABS_MOCK:
        logger.warning("OXYLABS MOCK MODE: serving fixture for %s", source)
        return _load_fixture(source)

    payload = {
        "source": source,
        "domain": domain,
        "query": query,
        "parse": True,
    }
    if context:
        payload["context"] = [{"key": k, "value": v} for k, v in context.items()]

    response = requests.post(
        config.OXYLABS_URL,
        auth=(config.OXYLABS_USERNAME, config.OXYLABS_PASSWORD),
        json=payload,
        timeout=90,
    )
    response.raise_for_status()
    content = response.json()["results"][0]["content"]

    _cache[cache_key] = content
    return content
