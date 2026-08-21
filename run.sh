#!/usr/bin/env bash
# Wrapper do motor (path novo ou legado detectado pela pasta do script).
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$APP_DIR/.venv"
# Compat: instalação antiga usa venv/ em vez de .venv/
if [ ! -x "$VENV_DIR/bin/python" ] && [ -x "$APP_DIR/venv/bin/python" ]; then
  VENV_DIR="$APP_DIR/venv"
fi
PY="$VENV_DIR/bin/python"
MAIN="$APP_DIR/scripts/verifica_leiautes_finaud.py"
LOG_DIR="$APP_DIR/logs"

export HOME="$APP_DIR"
export PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-$APP_DIR/runtime/browsers}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-$APP_DIR/runtime/cache}"
export LEIAUTES_DISABLE_STATUS_TAIL="${LEIAUTES_DISABLE_STATUS_TAIL:-1}"
# Destinatários vêm dos usuários com flag "Receber e-mail de alertas".
# Não force LEIAUTES_EMAIL_TEST_TO aqui.

if [ -f "$APP_DIR/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  source "$APP_DIR/.env"
  set +a
fi

mkdir -p "$LOG_DIR" "$PLAYWRIGHT_BROWSERS_PATH" "$XDG_CACHE_HOME"

log(){ echo "$(date '+%F %T') | $1" | tee -a "$LOG_DIR/execucao_$(date '+%Y%m%d').log"; }

if [ ! -x "$PY" ]; then
  log "Python do venv não encontrado: $PY"
  exit 2
fi
if [ ! -f "$MAIN" ]; then
  log "Script do motor não encontrado: $MAIN"
  exit 2
fi

if [[ "${1:-}" ]]; then
  export MONITOR_TEST_DATE="$1"
fi

log "=== INÍCIO leiautes (APP_DIR=$APP_DIR) ==="
set +e
cd "$APP_DIR"
"$PY" "$MAIN"
rc=$?
set -e

if [ "$rc" -eq 0 ]; then
  log "Execução concluída com sucesso (rc=0)."
  exit 0
fi
log "Falha na execução (rc=$rc)."
exit "$rc"
