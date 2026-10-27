# Tech Feed Podcast

Turns the latest TechCrunch articles into a short spoken podcast episode. Everything runs locally.

1. Reads the TechCrunch RSS feed and extracts the text of the top articles.
2. Summarizes each article into a ~20-second TLDR using a local LLM (Ollama, `llama3.1`).
3. Sends the combined summaries to you as a Telegram message. (Audio generation with Kokoro TTS is available in `audio_generator.py` but currently disabled in `script.py`.)

## Requirements

- Python 3.12
- [Ollama](https://ollama.com) installed and running, with the model pulled:
  ```bash
  ollama pull llama3.1
  ```

## Setup

This project uses [uv](https://docs.astral.sh/uv/). Dependencies are declared in [pyproject.toml](pyproject.toml) and locked in `uv.lock`:

```bash
uv sync
```

Create a `.env` file in the project root with your Telegram credentials (see [Telegram setup](#telegram-setup)):

```
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

The summaries are sent to your Telegram chat, prefixed with today's date. An article that fails to download or summarize is retried up to 3 times, then skipped.

## Telegram setup

1. Message `@BotFather` on Telegram, send `/newbot`, and copy the bot token.
2. Send any message to your new bot.
3. Open `https://api.telegram.org/bot<TOKEN>/getUpdates` and copy the `chat.id` value.
4. Put both values in `.env` as shown above.

## Configuration

Edit the constants at the top of [script.py](script.py):

- `FEED_URL`: RSS feed to read
- `MAX_ARTICLES`: number of articles to include (default 5)
- `MAX_CHARS`: max characters of each article sent to the LLM (default 6000, sized for the 8192-token context set in `llm.py`)

## Project layout

- [script.py](script.py): main pipeline (feed, extraction, summarize, send)
- [llm.py](llm.py): `write_script()` summarizes an article via Ollama and cleans the output for speech. Can also be run standalone: `python llm.py "article text"`
- [audio_generator.py](audio_generator.py): `create_audio()` turns a script into a WAV file with Kokoro
- [telegram_sender.py](telegram_sender.py): `send_message()` sends text to your Telegram chat (needs `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`, read from `.env`)
- [experiments/tts_demo.py](experiments/tts_demo.py): minimal Kokoro example
- [run.sh](run.sh): runs the pipeline with `uv run`
