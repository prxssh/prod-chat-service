#!/bin/sh

rm -f /tmp/prometheus_multiproc/*

exec uvicorn app.asgi:application \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 8 \
  --loop uvloop
