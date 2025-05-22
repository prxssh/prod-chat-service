# !/usr/bin/env bash

set -euo pipefail

COMPOSE_FILE=${COMPOSE_FILE:-"./docker/compose.yml"}
METRICS_URL=${METRICS_URL:-"http://localhost:80/metrics"}
INTERVAL=${INTERVAL:-10}

cleanup() {
  echo "\n[$(date '+%Y-%m-%d %H:%M:%S')] Stopping monitor..."
  kill "${TAIL_PID}" 2>/dev/null || true
  exit 0
}
trap cleanup SIGINT SIGTERM

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Tailing docker-compose logs for 'ERROR' using $COMPOSE_FILE"
docker-compose -f "$COMPOSE_FILE" logs -f --no-color \
  | grep --line-buffered -iE '"levelname":[[:space:]]*"ERROR"|level=error' &
TAIL_PID=$!

while true; do
  echo "\n[$(date '+%Y-%m-%d %H:%M:%S')] Top-5 counters from $METRICS_URL"
  curl -s "$METRICS_URL" |
    awk '/^[^#]/ { print $1, $2 }' |
    sort -k2 -nr |
    head -n 5
  sleep "$INTERVAL"
done
