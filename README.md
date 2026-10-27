# Tech Feed Podcast

Turns the latest TechCrunch articles into a short spoken podcast episode.

1. Reads the TechCrunch RSS feed and extracts the text of the top articles.
2. Summarizes each article into a ~20-second TLDR using an LLM on [Groq](https://groq.com) (`openai/gpt-oss-120b`). Articles are processed in parallel, a few at a time.
3. Sends the combined summaries to you as a Telegram message. (Audio generation with Kokoro TTS is available in `audio_generator.py` but currently disabled in `script.py`.)

Each run is traced with OpenTelemetry, so you can see how long each step takes.

## Requirements

- Python 3.12
- A Groq API key, from the [Groq console](https://console.groq.com/keys)
- A Telegram bot (see [Telegram setup](#telegram-setup))

## Setup

This project uses [uv](https://docs.astral.sh/uv/). Dependencies are declared in [pyproject.toml](pyproject.toml) and locked in `uv.lock`:

```bash
uv sync
```

Create a `.env` file in the project root with your keys:

```
GROQ_API_KEY=your-groq-key
TELEGRAM_BOT_TOKEN=your-token
TELEGRAM_CHAT_ID=123456789
```

If you enable audio generation, the first run downloads the Kokoro model (~300MB).

`requirements.txt` is kept for plain pip users. Note that `huggingface-hub` is capped below 2.0 because uv otherwise resolves a version that conflicts with `tokenizers`.

## Usage

```bash
./run.sh
```

or directly:

```bash
uv run python script.py
```

The summaries are sent to your Telegram chat, prefixed with today's date, in the same order as the feed. An article that fails to download or summarize is retried up to 3 times, then skipped.

## Tracing

[tracing.py](tracing.py) sets up OpenTelemetry. When the script finishes, every span is printed to the terminal as JSON, with a `start_time` and `end_time`:

- `main`: the whole run
- `article`: one per article (fetching plus summarizing), with the article URL in `article.link`
- `send_message`: sending to Telegram

Calls made with the `requests` library are traced automatically, except for Telegram's API, whose URLs contain the bot token.

## Telegram setup

1. Message `@BotFather` on Telegram, send `/newbot`, and copy the bot token.
2. Send any message to your new bot.
3. Open `https://api.telegram.org/bot<TOKEN>/getUpdates` and copy the `chat.id` value.
4. Put both values in `.env` as shown above.

## Configuration

Edit the constants at the top of [script.py](script.py):

- `FEED_URL`: RSS feed to read
- `MAX_ARTICLES`: number of feed entries to process (default 5). Articles that fail are skipped, so you may get fewer summaries.
- `MAX_CHARS`: max characters of each article sent to the LLM (default 6000)
- `MAX_PARALLEL`: how many articles are processed at once (default 3). Lower it if you hit Groq rate limits (HTTP 429 errors).

## Project layout

- [script.py](script.py): main pipeline (feed, extraction, summarize, send), run with `asyncio`
- [llm.py](llm.py): `write_script()` summarizes an article via Groq and cleans the output for speech. Can also be run standalone: `uv run python llm.py "article text"`
- [audio_generator.py](audio_generator.py): `create_audio()` turns a script into a WAV file with Kokoro
- [telegram_sender.py](telegram_sender.py): `send_message()` sends text to your Telegram chat (needs `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`, read from `.env`)
- [tracing.py](tracing.py): OpenTelemetry setup; provides the `tracer` used by the other files
- [experiments/tts_demo.py](experiments/tts_demo.py): minimal Kokoro example
- [run.sh](run.sh): runs the pipeline with `uv run`
