#!/bin/sh
set -eu

uvicorn app.main:app --host 127.0.0.1 --port 8000 &
api_pid=$!

cleanup() {
    kill "$api_pid" 2>/dev/null || true
    wait "$api_pid" 2>/dev/null || true
}

trap cleanup INT TERM EXIT
nginx -g "daemon off;" &
nginx_pid=$!

wait "$nginx_pid"