import time, asyncio
from datetime import date

import feedparser
from trafilatura import extract, fetch_url

from llm import write_script
from audio_generator import create_audio
from telegram_sender import send_message
from tracing import tracer

FEED_URL = "https://techcrunch.com/feed/"
MAX_ARTICLES = 5
MAX_CHARS = 6000
MAX_PARALLEL = 3

sem = asyncio.Semaphore(MAX_PARALLEL)

def fetch_article_text(link):
    downloaded = fetch_url(link)
    if not downloaded:
        return None
    return extract(downloaded)


def with_retries(fn, *args, attempts=3, delay=2):
    for attempt in range(1, attempts + 1):
        try:
            return fn(*args)
        except Exception:
            if attempt == attempts:
                raise
            time.sleep(delay * attempt)

async def summarize_article(link):
    # The semaphore caps how many articles are in flight at once
    async with sem:
        with tracer.start_as_current_span("article") as span:
            span.set_attribute("article.link", link)
            # print(link)
            try:
                # Both steps block, so run them in worker threads to keep the event loop free
                text = await asyncio.to_thread(with_retries, fetch_article_text, link)
                if not text:
                    print(f"Skipped {link}: couldn't extract text")
                    return None
                return await asyncio.to_thread(with_retries, write_script, text[:MAX_CHARS])
            except Exception as e:
                print(f"Skipped {link}: {type(e).__name__}: {e}")
                return None


async def parse_articles(entries):
    # gather keeps results in feed order, even though articles finish in any order
    results = await asyncio.gather(*(summarize_article(a.link) for a in entries))
    return [summary for summary in results if summary]


@tracer.start_as_current_span("main")
async def main():

    articles = await asyncio.to_thread(feedparser.parse, FEED_URL)

    summaries = await parse_articles(articles.entries[:MAX_ARTICLES])

    if not summaries:
        print("Couldn't extract any article text.")
        return

    script = "\n\n".join(summaries)
    # create_audio(script, filename=f"{date.today()}.wav")
    today_date = date.today()

    script = str(today_date) + "\n\n" + script
    await asyncio.to_thread(send_message, script)


if __name__ == "__main__":
    asyncio.run(main())
