#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ENV_FILE=${ENV_FILE:-"$ROOT_DIR/backend/.env"}
CREDENTIALS_FILE=${CREDENTIALS_FILE:-"$ROOT_DIR/backend/credentials.json"}
TOKEN_FILE=${TOKEN_FILE:-"$ROOT_DIR/backend/gmail-token.json"}
IMAGE_NAME=${IMAGE_NAME:-soa-demo}
CONTAINER_NAME=${CONTAINER_NAME:-soa-demo}
HOST_PORT=${HOST_PORT:-8080}

die() {
  printf 'Error: %s\n' "$1" >&2
  exit 1
}

command -v docker >/dev/null 2>&1 || die "Docker is not installed or not available in PATH"
[ -f "$ENV_FILE" ] || die "Environment file not found: $ENV_FILE"
[ -f "$CREDENTIALS_FILE" ] || die "Google credentials not found: $CREDENTIALS_FILE"
[ -f "$TOKEN_FILE" ] || die "Gmail token not found: $TOKEN_FILE"

encode_base64() {
  base64 < "$1" | tr -d '\n'
}

credentials_base64=$(encode_base64 "$CREDENTIALS_FILE")
token_base64=$(encode_base64 "$TOKEN_FILE")

printf 'Building image %s...\n' "$IMAGE_NAME"
docker build --no-cache --tag "$IMAGE_NAME" "$ROOT_DIR"

docker rm --force "$CONTAINER_NAME" >/dev/null 2>&1 || true

printf 'Starting container %s on port %s...\n' "$CONTAINER_NAME" "$HOST_PORT"
docker run --detach \
  --name "$CONTAINER_NAME" \
  --restart unless-stopped \
  --env-file "$ENV_FILE" \
  --env "GMAIL_CREDENTIALS_JSON_BASE64=$credentials_base64" \
  --env "GMAIL_TOKEN_JSON_BASE64=$token_base64" \
  --env "DATABASE_URL=sqlite:////app/data/absent_requests.db" \
  --publish "$HOST_PORT:80" \
  "$IMAGE_NAME"

printf 'Container is running: http://localhost:%s\n' "$HOST_PORT"

printf 'Creating default user...\n'
docker exec "$CONTAINER_NAME" python start_watch.py create-user --username test --email lmao@example.com --password test.com.vn