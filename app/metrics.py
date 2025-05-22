from prometheus_client import Counter, Gauge, Summary

total_messages = Counter("total_messages", "Total messages received")
active_connections = Gauge("active_connections", "Number of active WebSocket connections")
error_count = Counter("error_count", "Number of errors encountered")
shutdown_time = Summary("shutdown_time_seconds", "Time taken for graceful shutdown")
