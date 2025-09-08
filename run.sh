#!/usr/bin/env bash
set -euo pipefail

SITE_HOME="/home/tsalachtech.com.br"
APP_DIR="$SITE_HOME/apps/leiautes"
PUBLIC_DIR="$SITE_HOME/public_html/monitoramentos/leiautes"
VENV_DIR="$APP_DIR/venv"
LOG_DIR="$APP_DIR/logs"
TAIL="$PUBLIC_DIR/_status_tail.txt"
PY="$VENV_DIR/bin/python"
REQ="$APP_DIR/requirements.txt"
MAIN=$(ls -1 "$APP_DIR/scripts/"*.py 2>/dev/null | head -n1)

mkdir -p "$LOG_DIR"; touch "$TAIL"; chmod 664 "$TAIL"
log(){ echo "$(date '+%F %T') | $1" | tee -a "$LOG_DIR/execucao_$(date '+%Y%m%d').log"; }
tailw(){ echo "$(date '+%d/%m/%Y %H:%M:%S') | $1" > "$TAIL"; }

log "=== INÍCIO leiautes ==="
#tailw "Iniciando execução (leiautes)..."

# venv
if [ ! -x "$PY" ]; then
  python3 -m venv "$VENV_DIR"
  "$VENV_DIR/bin/pip" install --upgrade pip
fi

# requirements (se existir)
[ -f "$REQ" ] && "$VENV_DIR/bin/pip" install -r "$REQ" -q || true

# checagens mínimas
if [ -z "$MAIN" ]; then
  log "Nenhum script .py encontrado em $APP_DIR/scripts."
 # tailw "ERRO | Nenhum .py em scripts/"
  exit 2
fi

# executa
set +e
cd "$APP_DIR"
"$PY" "$MAIN"
rc=$?
set -e

if [ "$rc" -eq 0 ]; then
  log "Execução concluída com sucesso (rc=0)."
  #tailw "OK | Última execução: $(date '+%d/%m/%Y %H:%M:%S')"
  exit 0
else
  log "Falha na execução (rc=$rc)."
  #tailw "ERRO | Código $rc em $(date '+%d/%m/%Y %H:%M:%S')"
  exit "$rc"
fi
