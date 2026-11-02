import asyncio
import re

import feedparser
from trafilatura import extract, fetch_url

from .base import run_source, with_retries

NAME = "techcrunch"
FEED_URL = "https://techcrunch.com/feed/"
MAX_POSTS = 5
MAX_CHARS = 3000  # per article; several articles share one analysis prompt


def _mentions(topic, text):
    # Whole-word match, so "AI" doesn't match "said"
    return re.search(rf"\b{re.escape(topic)}\b", text, re.IGNORECASE)


def _fetch_text(link):
    downloaded = fetch_url(link)
    return extract(downloaded) if downloaded else None


async def get_posts(topic):
    feed = await asyncio.to_thread(feedparser.parse, FEED_URL)
    entries = [e for e in feed.entries if _mentions(topic, e.title + " " + e.get("summary", ""))]
    entries = entries[:MAX_POSTS]

    # Fetch all matching articles at once; one failed fetch doesn't stop the others
    texts = await asyncio.gather(
        *(with_retries(asyncio.to_thread, _fetch_text, e.link) for e in entries),
        return_exceptions=True,
    )
    return [
        {"title": e.title, "url": e.link, "text": t[:MAX_CHARS]}
        for e, t in zip(entries, texts)
        if isinstance(t, str) and t
    ]


async def run(topic):
    return await run_source(NAME, topic, get_posts)
