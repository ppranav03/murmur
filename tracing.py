from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.instrumentation.requests import RequestsInstrumentor
import datetime as dt
import os

current_dt = str(dt.datetime.now())
current_dt = current_dt.replace(":", "")
os.makedirs("logs", exist_ok=True)

provider = TracerProvider(resource=Resource.create({"service.name": "tech-feed-podcast"}))

log_file = open(f"logs/{current_dt}-log.json", "a", encoding="utf-8")
provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter(out = log_file)))
trace.set_tracer_provider(provider)

RequestsInstrumentor().instrument(excluded_urls="api.telegram.org")  # Telegram URLs contain the bot token

tracer = trace.get_tracer("tech-feed-podcast")
