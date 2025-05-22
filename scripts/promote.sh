# !/usr/bin/env bash
set -euo pipefail

CURRENT_COLOR=$(readlink -f docker/nginx/default.conf | xargs basename | sed 's/^default\.\(.*\)\.conf$/\1/')
TARGET_COLOR=$([[ "$CURRENT_COLOR" == "blue" ]] && echo green || echo blue)


if [[ "$TARGET_COLOR" == "blue" ]]; then
  APP_PORT=$APP_BLUE_PORT
else
  APP_PORT=$APP_GREEN_PORT
fi

APP_HOST="http://localhost:${APP_PORT}"
NGINX_LOCAL="http://localhost:${NGINX_PORT}"

echo "🔄 Promotion: $CURRENT_COLOR → $TARGET_COLOR"

echo "🚀 Starting app_${TARGET_COLOR}..."
docker-compose -f docker/compose.yml up -d --build app_${TARGET_COLOR}

echo "🧪 Running smoke tests on app_${TARGET_COLOR}: /healthz..."
sleep 3
curl -sf ${APP_HOST}/healthz \
  && echo "✅ ${TARGET_COLOR} /healthz OK (via host)" \
  || (echo "❌ ${TARGET_COLOR} /healthz failed" && exit 1)

echo "⏳ Waiting for app_${TARGET_COLOR} to become ready (/readyz)..."
for i in {1..10}; do
  if curl -sf ${APP_HOST}/readyz > /dev/null; then
    echo "✅ ${TARGET_COLOR} /readyz ready"
    break
  else
    echo "  Not ready yet... retrying"
    sleep 1
  fi
done

echo "🔁 Switching Nginx to $TARGET_COLOR..."
ln -nfs default.${TARGET_COLOR}.conf devops/nginx/default.conf
docker-compose -f docker/compose.yml exec -T nginx nginx -s reload

curl -sf ${NGINX_LOCAL}/ping \
  && echo "✅ Nginx /healthz OK" \
  || (echo "❌ Nginx /healthz failed" && exit 1)

echo "🧹 Stopping app_${CURRENT_COLOR}..."
docker-compose -f docker/compose.yml stop app_${CURRENT_COLOR}
docker-compose -f docker/compose.yml rm -f app_${CURRENT_COLOR}

echo "✅ Promotion complete: Now serving from $TARGET_COLOR"
