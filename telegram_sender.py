import os
from dotenv import load_dotenv
import sys
import requests
from tracing import tracer

load_dotenv()
API_URL = "https://api.telegram.org/bot{token}/sendMessage"
MAX_LEN = 4096  # Telegram's per-message limit

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

@tracer.start_as_current_span("send_message")
def send_message(text = None):
    if text is None:
        print("Value Error: send_message must take in parameter <text>.")
        raise ValueError

    if not BOT_TOKEN:
        print("Key Error: TELEGRAM_BOT_TOKEN not found\n")
        raise KeyError
    if not CHAT_ID:
        print("Key Error: TELEGRAM_CHAT_ID not found\n")
        raise KeyError
    
    for start in range(0, len(text), MAX_LEN):
        response = requests.post(
            url= API_URL.format(token=BOT_TOKEN),
            data={"chat_id": CHAT_ID, "text": text[start:start + MAX_LEN]},
            timeout=30,
        )
        response.raise_for_status()
    print("Sent message to Telegram")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Usage warning: python telegram_sender.py <message>")
    send_message(" ".join(sys.argv[1:]))
