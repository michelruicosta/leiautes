#!/bin/bash
set -euo pipefail

BASE="/home/bacen.com.br/public_html/monitoramentos/leiautes"
LOGDIR="$BASE/logs"
LOG="$LOGDIR/execucao_cron.log"
SCRIPT_DIR="$BASE/scripts"
PY="$BASE/venv/bin/python"

# Playwright/cache agora em runtime/
export HOME="$BASE"
export PLAYWRIGHT_BROWSERS_PATH="$BASE/runtime/browsers"
export XDG_CACHE_HOME="$BASE/runtime/cache"

mkdir -p "$LOGDIR" "$PLAYWRIGHT_BROWSERS_PATH" "$XDG_CACHE_HOME"
touch "$LOG"

# se quiser aceitar uma data opcional como argumento: run.sh 27/08/2025
if [[ ${1:-} ]]; then export MONITOR_TEST_DATE="$1"; fi

{
  echo ""
  echo "===== START $(date) ====="
  echo "whoami: $(whoami)"
  echo "pwd antes do cd: $(pwd)"
  echo "PATH: ${PATH}"
  echo "Python apontado: $PY"

  cd "$SCRIPT_DIR"
  echo "pwd após cd: $(pwd)"

  echo "Python version (venv):"
  "$PY" --version || echo "Python não encontrado"

  echo "Executando verifica_leiautes_finaud.py..."
  "$PY" verifica_leiautes_finaud.py || true

  echo "Exit code do Python: $?"
  echo "===== END $(date) ====="
} >> "$LOG" 2>&1
