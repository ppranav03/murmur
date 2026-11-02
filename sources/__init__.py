from . import hackernews, techcrunch

# Every source is a module with a NAME and an async run(topic) that returns a result dict.
# The orchestrator only loops over this list, so adding a source means adding it here.
SOURCES = [techcrunch, hackernews]
