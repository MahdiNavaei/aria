#!/usr/bin/env bash
set -euo pipefail

docker compose up -d

services=(aria-redpanda aria-redis aria-qdrant)
for svc in "${services[@]}"; do
  echo "Waiting for $svc to be healthy..."
  until [ "$(docker inspect -f '{{.State.Health.Status}}' "$svc" 2>/dev/null)" = "healthy" ]; do
    sleep 2
  done
  echo "$svc is healthy"
done

if [ -z "${DEV_CMD:-}" ]; then
  echo "Set DEV_CMD to start the dev server (example: DEV_CMD='uvicorn aria.api.rest.app:app --reload')"
  exit 0
fi

eval "$DEV_CMD"
