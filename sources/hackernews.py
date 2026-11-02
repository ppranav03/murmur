import asyncio
import html
import re
import time

import requests

from .base import run_source, with_retries

NAME = "hackernews"
SEARCH_URL = "https://hn.algolia.com/api/v1/search"
ITEM_URL = "https://hn.algolia.com/api/v1/items/{id}"
MAX_POSTS = 5
MAX_COMMENTS = 5
MAX_COMMENT_CHARS = 500


def _get_json(url, params=None):
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def _strip_html(text):
    # HN comments come as HTML
    return html.unescape(re.sub(r"<[^>]+>", " ", text or "")).strip()


def _top_comments(story_id):
    item = _get_json(ITEM_URL.format(id=story_id))
    comments = [_strip_html(c["text"]) for c in item.get("children", []) if c.get("text")]
    return [c[:MAX_COMMENT_CHARS] for c in comments[:MAX_COMMENTS]]


async def get_posts(topic):
    # Stories from the last 24 hours, most upvoted first
    since = int(time.time()) - 24 * 60 * 60
    params = {"query": topic, "tags": "story", "numericFilters": f"created_at_i>{since}", "hitsPerPage": 30}
    data = await with_retries(asyncio.to_thread, _get_json, SEARCH_URL, params)
    stories = sorted(data["hits"], key=lambda s: s.get("points") or 0, reverse=True)[:MAX_POSTS]

    # Comments carry the sentiment, so fetch them for every story at once
    comment_lists = await asyncio.gather(
        *(with_retries(asyncio.to_thread, _top_comments, s["objectID"]) for s in stories),
        return_exceptions=True,
    )

    posts = []
    for story, comments in zip(stories, comment_lists):
        if isinstance(comments, Exception):
            comments = []
        lines = [f"{story.get('points') or 0} points, {story.get('num_comments') or 0} comments"]
        lines += [f"- {c}" for c in comments]
        posts.append({
            "title": story["title"],
            "url": f"https://news.ycombinator.com/item?id={story['objectID']}",
            "text": "\n".join(lines),
        })
    return posts


async def run(topic):
    return await run_source(NAME, topic, get_posts)
