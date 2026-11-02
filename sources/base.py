import asyncio
import time

from opentelemetry.trace import Status, StatusCode

from llm import analyze_posts
from tracing import tracer


async def with_retries(fn, *args, attempts=3, delay=2):
    for attempt in range(1, attempts + 1):
        try:
            return await fn(*args)
        except Exception:
            if attempt == attempts:
                raise
            await asyncio.sleep(delay * attempt)  # unlike time.sleep, lets other tasks keep running


async def run_source(name, topic, get_posts):
    # Shared by every source: collect posts, analyse them, and never raise.
    # Raw posts stay in here; only the small analysis goes back to the orchestrator.
    start = time.perf_counter()
    with tracer.start_as_current_span("source") as span:
        span.set_attribute("source.name", name)
        span.set_attribute("topic", topic)
        try:
            with tracer.start_as_current_span("collect"):
                posts = await get_posts(topic)
            span.set_attribute("post_count", len(posts))
            
            if not posts:
                # Nothing about this topic today. That's not an error.
                return _result(name, "empty", start)

            with tracer.start_as_current_span("analyze"):
                analysis = await with_retries(analyze_posts, topic, name, posts)
            return _result(name, "ok", start, post_count=len(posts), **analysis)

        except Exception as e:
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            return _result(name, "failed", start, error=f"{type(e).__name__}: {e}")


def _result(name, status, start, **fields):
    latency_ms = int((time.perf_counter() - start) * 1000)
    return {"source": name, "status": status, "latency_ms": latency_ms, **fields}
