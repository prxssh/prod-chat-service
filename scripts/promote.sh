# !/usr/bin/env bash
set -euo pipefail

CURRENT_COLOR=$(readlink -f docker/nginx/default.conf | xargs basename | sed 's/^default\.\(.*\)\.conf$/\1/')
TARGET_COLOR=$([[ "$CURRENT_COLOR" == "blue" ]] && echo green || echo blue)

NGINX_LOCAL="http://localhost:80"
APP_PORT=$([[ "$TARGET_COLOR" == "blue" ]] && echo 6969 || echo 6970)
APP_HOST="http://localhost:${APP_PORT}"

echo "🔄 Promotion: $CURRENT_COLOR → $TARGET_COLOR"

echo "🚀 Starting app_${TARGET_COLOR}..."
docker-compose -f docker/compose.yml up -d --build app_${TARGET_COLOR}

echo "🧪 Running smoke tests on app_${TARGET_COLOR}..."
sleep 3
curl -sf ${APP_HOST}/ping \
  && echo "✅ ${TARGET_COLOR} /ping OK (via host)" \
  || (echo "❌ ${TARGET_COLOR} /ping failed" && exit 1)

echo "🔁 Switching Nginx to $TARGET_COLOR..."
ln -nfs default.${TARGET_COLOR}.conf docker/nginx/default.conf
docker-compose -f docker/compose.yml exec -T nginx nginx -s reload

curl -sf ${NGINX_LOCAL}/healthz \
  && echo "✅ Nginx /healthz OK" \
  || (echo "❌ Nginx /healthz failed" && exit 1)

echo "🧹 Stopping app_${CURRENT_COLOR}..."
docker-compose -f docker/compose.yml stop app_${CURRENT_COLOR}
docker-compose -f docker/compose.yml rm -f app_${CURRENT_COLOR}

echo "✅ Promotion complete: Now serving from $TARGET_COLOR"
