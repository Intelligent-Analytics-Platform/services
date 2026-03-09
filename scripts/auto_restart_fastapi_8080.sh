#!/usr/bin/env bash
set -euo pipefail

# Health-check and auto-restart helper for a FastAPI service expected on port 8080.
# Usage examples:
#   START_CMD='cd /Users/lee/services/apps/meta && uv run uvicorn meta.app:app --host 0.0.0.0 --port 8080' ./scripts/auto_restart_fastapi_8080.sh --once
#   START_CMD='cd /Users/lee/services/apps/meta && uv run uvicorn meta.app:app --host 0.0.0.0 --port 8080' ./scripts/auto_restart_fastapi_8080.sh --watch --interval 10

PORT="${PORT:-8080}"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:${PORT}/docs}"
START_CMD="${START_CMD:-}"
START_TIMEOUT="${START_TIMEOUT:-30}"
WORK_DIR="${WORK_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
RUN_DIR="${RUN_DIR:-${WORK_DIR}/.run}"
LOG_DIR="${LOG_DIR:-${WORK_DIR}/logs}"
PID_FILE="${PID_FILE:-${RUN_DIR}/fastapi-${PORT}.pid}"
LOG_FILE="${LOG_FILE:-${LOG_DIR}/fastapi-${PORT}.log}"

MODE="once"
INTERVAL=15

while [[ $# -gt 0 ]]; do
  case "$1" in
    --once)
      MODE="once"
      shift
      ;;
    --watch)
      MODE="watch"
      shift
      ;;
    --interval)
      INTERVAL="$2"
      shift 2
      ;;
    *)
      echo "Unknown arg: $1" >&2
      exit 2
      ;;
  esac
done

mkdir -p "$RUN_DIR" "$LOG_DIR"

ts() {
  date '+%Y-%m-%d %H:%M:%S'
}

log() {
  echo "[$(ts)] $*"
}

is_healthy() {
  local code
  code="$(curl --max-time 5 -s -o /dev/null -w '%{http_code}' "$HEALTH_URL" || true)"
  [[ "$code" == "200" ]]
}

pid_alive() {
  [[ -f "$PID_FILE" ]] || return 1
  local pid
  pid="$(cat "$PID_FILE" 2>/dev/null || true)"
  [[ -n "$pid" ]] || return 1
  kill -0 "$pid" 2>/dev/null
}

stop_if_running() {
  if pid_alive; then
    local pid
    pid="$(cat "$PID_FILE")"
    log "Stopping stale process pid=$pid"
    kill "$pid" 2>/dev/null || true
    sleep 1
    if kill -0 "$pid" 2>/dev/null; then
      kill -9 "$pid" 2>/dev/null || true
    fi
  fi
  rm -f "$PID_FILE"
}

start_service() {
  if [[ -z "$START_CMD" ]]; then
    log "START_CMD is empty; cannot restart automatically."
    log "Example: START_CMD='cd /Users/lee/services/apps/meta && uv run uvicorn meta.app:app --host 0.0.0.0 --port 8080'"
    return 1
  fi

  log "Starting service with START_CMD"
  nohup zsh -lc "$START_CMD" >>"$LOG_FILE" 2>&1 &
  local pid=$!
  echo "$pid" > "$PID_FILE"

  local i
  for ((i=1; i<=START_TIMEOUT; i++)); do
    if is_healthy; then
      log "Service healthy at ${HEALTH_URL} (pid=$pid)"
      return 0
    fi
    sleep 1
  done

  log "Service failed health check within ${START_TIMEOUT}s"
  return 1
}

check_and_recover() {
  if is_healthy; then
    log "Healthy: ${HEALTH_URL}"
    return 0
  fi

  log "Unhealthy: ${HEALTH_URL}; attempting restart"
  stop_if_running
  start_service
}

if [[ "$MODE" == "once" ]]; then
  check_and_recover
  exit $?
fi

log "Watch mode enabled, interval=${INTERVAL}s"
while true; do
  check_and_recover || true
  sleep "$INTERVAL"
done
