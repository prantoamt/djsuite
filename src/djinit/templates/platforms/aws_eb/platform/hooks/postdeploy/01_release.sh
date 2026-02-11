#!/usr/bin/env bash
set -euo pipefail
set -x

echo "[release] locating app container..."

resolve_cid() {
  # 1) EB typically names the container "app"
  docker ps -q -f "name=^/app$" | head -n1 || true
  # 2) Fallback: anything publishing host port 80
  [ -n "${_CID:-}" ] || _CID="$(docker ps -q -f "publish=80" | head -n1 || true)"
  # 3) Fallback: the EB-built image tag
  [ -n "${_CID:-}" ] || _CID="$(docker ps -q -f "ancestor=aws_beanstalk/current-app:latest" | head -n1 || true)"
  echo "${_CID:-}"
}

CID=""
for i in $(seq 1 60); do                # wait up to ~60s
  CID="$(resolve_cid)"
  if [ -n "$CID" ]; then
    echo "[release] found container: $CID"
    break
  fi
  sleep 2
done

if [ -z "$CID" ]; then
  echo "[release] ERROR: app container not found. Listing containers:"
  docker ps -a
  exit 1
fi

docker exec "$CID" /bin/sh -lc "/app/release.sh"

echo "[release] done"
