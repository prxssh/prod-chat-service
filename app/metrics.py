import os
from prometheus_client import (
    Counter,
    Gauge,
    Summary,
    CollectorRegistry,
    multiprocess,
)

registry = CollectorRegistry()
if "PROMETHEUS_MULTIPROC_DIR" in os.environ:
    multiprocess.MultiProcessCollector(registry)

total_messages = Counter(
    "total_messages", "Total messages received", registry=registry
)

active_connections = Gauge(
    "active_connections", "Number of active WebSocket connections", registry=registry
)

error_count = Counter(
    "error_count", "Number of errors encountered", registry=registry
)

shutdown_time = Summary(
    "shutdown_time_seconds", "Time taken for graceful shutdown", registry=registry
)
