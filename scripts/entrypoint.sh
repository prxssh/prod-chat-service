#!/bin/sh

rm -f /tmp/prometheus_multiproc/*

# 4 ASGI workers processes -> parallelizes CPU bound work across 4 cores
# TODO: We can also have a thread pool workers, of say 20 threads, to offload
# I/O bound work without blocking the event loop.
exec uvicorn app.asgi:application \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 5 \
  --ws websockets \
  --limit-concurrency 1024 \
  --timeout-keep-alive 5 \
  --timeout-graceful-shutdown 30 \
  --loop uvloop
