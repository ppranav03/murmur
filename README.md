# Murmur

Murmur reads the latest TechCrunch articles, summarizes each one into a short spoken-style TLDR with an LLM, and sends the digest to Telegram every morning.

It's growing into a multi-user trend tracker: pick a topic, and Murmur analyzes what several sources are saying about it and emails you a daily digest.

## Results so far

Each run is traced with OpenTelemetry, so every change is measured. Same pipeline, 5 articles:

| Version | Model | Articles | Run time |
|---|---|---|---|
| v1 | Ollama `llama3.1`, local | one at a time | 4 min 32 s |
| current | Groq `openai/gpt-oss-120b` | one at a time | 9.5 s |
| current | Groq `openai/gpt-oss-120b` | 3 in parallel | not measured yet |

Summarizing is still most of the run time: about 1.5 s per article, against about 0.06 s for a typical fetch.

## What's done

- **Pipeline.** Reads the TechCrunch RSS feed, extracts article text with trafilatura, summarizes each article into a ~50-word NPR-style TLDR, and sends the result to Telegram, prefixed with the date.
- **Hosted model.** Summaries come from Groq through LangChain (`ChatGroq`), so Murmur no longer needs a local Ollama server.
- **Parallel processing.** Articles are processed concurrently with `asyncio`: blocking work runs in worker threads, and a semaphore limits how many run at once.
- **Reliability.** Fetches and summaries are retried up to 3 times with backoff. An article that still fails is skipped, so it doesn't stop the run.
- **Tracing.** OpenTelemetry spans for the whole run, each article, and its fetch and summarize steps, written to `logs/`. Failed articles are recorded on their spans.
- **Output cleanup.** LLM output is stripped of markdown, preambles and Unicode dashes so it reads cleanly aloud.
- **Audio (parked).** `audio_generator.py` can turn the digest into a WAV file with Kokoro TTS, but it's switched off for now.

## Goals

- [ ] Run on a schedule with GitHub Actions, so it doesn't depend on a laptop being on
- [ ] Split sources into a `sources/` package with a shared interface, and add Hacker News
- [ ] Let users sign up with an email and a topic, analyze each topic once, and send digests by email
- [ ] Publish digests to a static site on GitHub Pages
- [ ] Merge results from several sources into one digest per topic
- [ ] Track run time, cost per run and failure rate, and check that digest claims match real posts

## Setup

Requires Python 3.12 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

Create a `.env` file in the project root:

```
GROQ_API_KEY=your-groq-key
TELEGRAM_BOT_TOKEN=your-token
TELEGRAM_CHAT_ID=123456789
```

- **Groq key:** create one in the [Groq console](https://console.groq.com/keys).
- **Telegram:** message `@BotFather`, send `/newbot` and copy the token. Send any message to your new bot, then open `https://api.telegram.org/bot<TOKEN>/getUpdates` and copy the `chat.id` value.

## Usage

```bash
./run.sh
```

or directly:

```bash
uv run python script.py
```

Each run writes its trace to a new file in `logs/`. Telegram API calls are left out of the trace because their URLs contain the bot token.

## Configuration

Constants at the top of [script.py](script.py):

- `FEED_URL`: RSS feed to read
- `MAX_ARTICLES`: number of feed entries to process (default 5). Failed articles are skipped, so you may get fewer summaries.
- `MAX_CHARS`: max characters of each article sent to the LLM (default 6000)
- `MAX_PARALLEL`: how many articles are processed at once (default 3). Lower it if Groq returns rate-limit errors (HTTP 429).

## Project layout

- [script.py](script.py): the pipeline (feed, extraction, summarize, send)
- [llm.py](llm.py): `write_script()` summarizes an article via Groq and cleans the output. Can also run standalone: `uv run python llm.py "article text"`
- [telegram_sender.py](telegram_sender.py): `send_message()` sends text to your Telegram chat
- [tracing.py](tracing.py): OpenTelemetry setup; provides the `tracer` used by the other files
- [audio_generator.py](audio_generator.py): `create_audio()` turns text into a WAV file with Kokoro (currently unused)
- [run.sh](run.sh): runs the pipeline with `uv run`

`requirements.txt` is out of date; install with uv.
