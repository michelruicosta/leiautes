#!/bin/bash
set -euo pipefail
APP="/home/tsalachtech.com.br/apps/leiautes"
LOG="$APP/logs"
find "$LOG" -type f -name "monitor_leiautes_*.log" -mtime +14 -delete 2>/dev/null || true
if [ -f "$LOG/execucao_cron.log" ]; then
  s=$(stat -c%s "$LOG/execucao_cron.log" 2>/dev/null || echo 0)
  if [ "$s" -gt 5242880 ]; then
    mv "$LOG/execucao_cron.log" "$LOG/execucao_cron_$(date +%Y%m%d_%H%M%S).log"
    : > "$LOG/execucao_cron.log"
  fi
fi
