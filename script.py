import asyncio
import operator
import sys
from datetime import date
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph

from sources import SOURCES
from tracing import tracer

TOPIC = "Meta"


class State(TypedDict):
    topic: str
    # Source nodes run in parallel and each adds one result; operator.add merges them into one list
    results: Annotated[list[dict], operator.add]


def source_node(source):
    async def node(state):
        result = await source.run(state["topic"])
        return {"results": [result]}
    return node


def report(state):
    print(f"Murmur: {state['topic']} ({date.today()})\n")

    # Parallel nodes finish in any order, so print in the order SOURCES lists them
    order = [s.NAME for s in SOURCES]
    for r in sorted(state["results"], key=lambda r: order.index(r["source"])):
        print(f"[{r['source']}] {r['status']} in {r['latency_ms'] / 1000:.1f} s")
        if r["status"] == "failed":
            print(f"  Error: {r['error']}")
        elif r["status"] == "ok":
            print(f"  Posts analysed: {r['post_count']}")
            print(f"  Sentiment: {r['sentiment']}")
            print(f"  Themes: {', '.join(r['themes'])}")
            print("  Notable posts:")
            for p in r["notable_posts"]:
                print(f"    - {p['title']} ({p['url']})")
                print(f"      {p['why']}")
        print()
    return {}


def build_graph():
    # START fans out to every source at once; "report" waits until all of them have finished
    graph = StateGraph(State)
    graph.add_node("report", report)
    for source in SOURCES:
        graph.add_node(source.NAME, source_node(source))
        graph.add_edge(START, source.NAME)
        graph.add_edge(source.NAME, "report")
    graph.add_edge("report", END)
    return graph.compile()


@tracer.start_as_current_span("main")
async def main():
    graph = build_graph()
    await graph.ainvoke({"topic": TOPIC, "results": []})


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # posts often contain characters Windows consoles can't print
    asyncio.run(main())
