# !/usr/bin/env bash
set -euo pipefail

CURRENT_COLOR=$(readlink -f docker/nginx/default.conf | xargs basename | sed 's/^default\.\(.*\)\.conf$/\1/')
TARGET_COLOR=$([[ "$CURRENT_COLOR" == "blue" ]] && echo green || echo blue)

echo "Promotion: $CURRENT_COLOR → $TARGET_COLOR"

docker-compose -f docker/compose.yml up -d --build app_${TARGET_COLOR}

ln -nfs default.${TARGET_COLOR}.conf docker/nginx/default.conf

docker-compose -f docker/compose.yml exec -T nginx nginx -s reload

echo "Traffic now routing to: $TARGET_COLOR"
