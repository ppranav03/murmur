import time
from datetime import date

import feedparser
from trafilatura import extract, fetch_url

from llm import write_script
from audio_generator import create_audio
from telegram_sender import send_message
from tracing import tracer

FEED_URL = "https://techcrunch.com/feed/"
MAX_ARTICLES = 5
MAX_CHARS = 6000  # keeps each prompt well inside the model's 8192-token context


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

@tracer.start_as_current_span("main")
def main():
    articles = feedparser.parse(FEED_URL)

    summaries = []
    for a in articles.entries:

        if len(summaries) >= MAX_ARTICLES:
            break
        # print(a.link)
        with tracer.start_as_current_span("article") as span:
            span.set_attribute("article.link", a.link)
            try:
                text = with_retries(fetch_article_text, a.link)
                if not text:
                    print("Skipped: couldn't extract text")
                    continue
                summary = with_retries(write_script, text[:MAX_CHARS])
            except Exception as e:
                print(f"Skipped: {type(e).__name__}: {e}")
                continue
            summaries.append(summary)

    if not summaries:
        print("Couldn't extract any article text.")
        return

    script = "\n\n".join(summaries)
    # create_audio(script, filename=f"{date.today()}.wav")
    today_date = date.today()

    script = str(today_date) + "\n\n" + script
    send_message(script)


if __name__ == "__main__":
    main()
