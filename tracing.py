from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.instrumentation.requests import RequestsInstrumentor

provider = TracerProvider(resource=Resource.create({"service.name": "tech-feed-podcast"}))
provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
trace.set_tracer_provider(provider)

RequestsInstrumentor().instrument(excluded_urls="api.telegram.org")  # Telegram URLs contain the bot token

tracer = trace.get_tracer("tech-feed-podcast")
