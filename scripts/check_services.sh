#!/usr/bin/env bash
# Check health status and show URLs for all platform services.
# Usage:
#   ./scripts/check_services.sh
#   HOST=192.168.1.10 ./scripts/check_services.sh

HOST="${HOST:-127.0.0.1}"
TIMEOUT="${TIMEOUT:-5}"

declare -a NAMES=(meta identity vessel data analytics)
declare -a PORTS=(8000 8001 8002 8003 8004)

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

printf '\n%-12s %-8s %-40s %s\n' "服务" "端口" "Docs URL" "状态"
printf '%s\n' "$(printf '%0.s─' {1..70})"

all_ok=true

for i in "${!NAMES[@]}"; do
  name="${NAMES[$i]}"
  port="${PORTS[$i]}"
  docs_url="http://${HOST}:${port}/docs"
  health_url="http://${HOST}:${port}/"

  http_code="$(curl --max-time "$TIMEOUT" -s -o /dev/null -w '%{http_code}' "$health_url" 2>/dev/null)" || http_code="000"

  if [[ "$http_code" == "200" ]]; then
    status="${GREEN}● 运行中${NC}"
  else
    status="${RED}✗ 不可达 (HTTP ${http_code})${NC}"
    all_ok=false
  fi

  printf "%-12s %-8s %-40s ${status}\n" "$name" "$port" "$docs_url"
done

printf '\n'
if $all_ok; then
  printf "${GREEN}所有服务运行正常。${NC}\n\n"
else
  printf "${RED}部分服务不可达，请检查进程或 K8s Pod 状态。${NC}\n\n"
fi
