# Deploy no servidor — leiautes_bacen

Última atualização: **2026-07-22** (robô novo em paralelo; antigo ainda ativo)

**Referência de processo:** Normativos — `documentacao/manual_publicacao_site.md` Cap. 12 (repo normativos_ia).

---

## Endereço em produção

| Item | Valor |
|------|-------|
| **URL** | `https://leiautes-bacen.finaudapps.com.br` |
| **Código** | `/srv/finaud/tec/leiautes_bacen/` |
| **API interna** | `127.0.0.1:8003` |
| **systemd** | `leiautes_bacen-api` |
| **CyberPanel home** | `/home/leiautes-bacen.finaudapps.com.br/` |
| **Robô novo** | path acima — cron root **paralelo** (teste) |
| **Robô legado** | `/home/tsalachtech.com.br/apps/leiautes/` — **ainda ativo** (não desligar) |

### Portas Finaud (já em uso)

| App | Porta |
|-----|-------|
| Auditoria | `8000` |
| Normativos | `8001` |
| Portal Auth | `8002` |
| **Leiautes Bacen** | **`8003`** |

---

## Checklist

| # | Passo | Status |
|---|--------|--------|
| 1 | DNS Cloudflare + CyberPanel + SSL Let's Encrypt | ✅ (proxy laranja; LE produção `YE2`) |
| 2 | Código em `/srv/finaud/tec/leiautes_bacen/` | ✅ |
| 3 | `.env` + venv + build | ✅ |
| 4 | systemd `leiautes_bacen-api` + health `:8003` | ✅ |
| 5 | vHost Conf (dist + `/api/` → 8003) | ✅ |
| 6 | Cloudflare laranja após SSL | ✅ |
| 7 | Validação login / telas | **pendente Michel** (`michel@`) |
| 8 | Card portal finaudapps | ✅ (Michel — outro chat) |
| 9 | Robô novo em paralelo (cron root + deps motor) | ✅ 2026-07-22 — **antigo ainda ativo** |
| 10 | Desligar cron legado (`tsala9334` / `paine6949`) | **não fazer** até Michel validar |

### Validação E2E (2026-07-22)

| Check | Resultado |
|-------|-----------|
| DNS → Cloudflare | ✅ `104.21.37.129` / `172.67.208.59` |
| HTTPS origem | ✅ Let's Encrypt `CN=YE2` (não staging) |
| Front `https://…/` | ✅ HTTP 200 · HTML React (`#root` + assets) |
| API `https://…/api/health` | ✅ `{"status":"ok","version":"0.1.0-mvp"}` |
| `systemctl is-active leiautes_bacen-api` | ✅ `active` |
| `curl http://127.0.0.1:8003/health` | ✅ 200 |

**Nota SSL:** o primeiro `cyberpanel issueSSL` deixou certificado **staging** / self-signed no path do vHost → Cloudflare **526**. Corrigido com `acme.sh --issue --force --server letsencrypt` + `--install-cert` em `/etc/letsencrypt/live/leiautes-bacen.finaudapps.com.br/`.

---

## `.env` mínimo

```env
AUTH_SECRET_KEY=...
AUTH_COOKIE_SECURE=1
AUTH_COOKIE_DOMAIN=.finaudapps.com.br
LEIAUTES_FRONTEND_URL=https://leiautes-bacen.finaudapps.com.br
LEIAUTES_DB_PATH=/srv/finaud/tec/leiautes_bacen/dados/leiautes.db
PORTAL_AUTH_URL=http://127.0.0.1:8002
PORTAL_URL=https://finaudapps.com.br
LEIAUTES_EMAIL_TEST_TO=michel@finaud.com.br
LEIAUTES_DISABLE_STATUS_TAIL=1
PLAYWRIGHT_BROWSERS_PATH=/srv/finaud/tec/leiautes_bacen/runtime/browsers
```

---

## systemd

Arquivo: `/etc/systemd/system/leiautes_bacen-api.service`

```ini
[Unit]
Description=Leiautes Bacen API
After=network.target

[Service]
WorkingDirectory=/srv/finaud/tec/leiautes_bacen
EnvironmentFile=/srv/finaud/tec/leiautes_bacen/.env
ExecStart=/srv/finaud/tec/leiautes_bacen/.venv/bin/python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8003 --app-dir backend --proxy-headers
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable --now leiautes_bacen-api
curl -s http://127.0.0.1:8003/health
```

---

## DNS Cloudflare (ordem obrigatória)

1. Registro **A** `leiautes-bacen` → IP da VPS (`31.97.82.203`) com proxy **cinza (DNS only)**
2. Emitir SSL Let's Encrypt no CyberPanel
3. Só então ativar proxy **laranja**

---

## vHost (espelho Normativos)

- `docRoot` → `/srv/finaud/tec/leiautes_bacen/frontend/dist`
- `extprocessor 127.0.0.1:8003` (proxy)
- Rewrite: `/api/` → `http://127.0.0.1:8003/` + SPA `index.html`

---

## Robô — paralelo (2026-07-22)

**Status:** robô **novo** agendado no root; robô **antigo** continua nos crons de `tsala9334` e `paine6949`.  
Espelho do Cap. 12 Normativos. **Não desligar o antigo** até uma execução do novo estar validada por Michel.

### Inventário cron (só leitura — legado intacto)

| Usuário | Linha leiautes | Status |
|---------|----------------|--------|
| **tsala9334** | `0 18 * * 1-5 …/apps/leiautes/run.sh` | **ativo** (legado) |
| **paine6949** | `0 18 * * 1-5 …/apps/leiautes/run.sh` | **ativo** (legado) |
| **root** | `0 18 * * 1-5` + `flock` → `/srv/finaud/tec/leiautes_bacen/` | **ativo** (teste paralelo) |

### Cron novo (root)

```cron
# [leiautes_bacen] teste paralelo — Seg-Sex 18h; e-mail so michel@ via LEIAUTES_EMAIL_TEST_TO; antigo permanece
0 18 * * 1-5 flock -n /srv/finaud/tec/leiautes_bacen/.robo.lock -c "cd /srv/finaud/tec/leiautes_bacen && set -a && . ./.env && set +a && export LEIAUTES_DISABLE_STATUS_TAIL=1 LEIAUTES_EMAIL_TEST_TO=michel@finaud.com.br HOME=/srv/finaud/tec/leiautes_bacen && .venv/bin/python scripts/verifica_leiautes_finaud.py >> /srv/finaud/tec/leiautes_bacen/logs/cron-teste-michel.log 2>&1"
```

- `flock` evita duas execuções do **novo** ao mesmo tempo.
- `LEIAUTES_EMAIL_TEST_TO=michel@finaud.com.br` redireciona destinatários do `config_email.json` só para Michel (quando o envio estiver ativo).
- Log: `/srv/finaud/tec/leiautes_bacen/logs/cron-teste-michel.log`
- Backup crontab root: `/root/backup-cron-leiautes/`

### Motor / deps

| Item | Detalhe |
|------|---------|
| Script | `scripts/verifica_leiautes_finaud.py` |
| Wrapper | `run.sh` (path relativo à pasta do app) |
| Deps motor | `requirements.txt` no `.venv` (playwright, requests, …) |
| Browsers | symlink `runtime/browsers` → legado (`chromium-1187`, ~919M — sem duplicar) |
| SMTP | `config/config_email.json` copiado do legado (perms `600`, fora do git) |
| Compat Py 3.9 | `from __future__ import annotations` no motor (venv do app é 3.9; legado usa 3.11) |

### `.env` (robô)

```env
LEIAUTES_EMAIL_TEST_TO=michel@finaud.com.br
LEIAUTES_DISABLE_STATUS_TAIL=1
PLAYWRIGHT_BROWSERS_PATH=/srv/finaud/tec/leiautes_bacen/runtime/browsers
```

### Disparo manual

| Via | Como |
|-----|------|
| **Tela** | App → **Robô** → executar (API com `enviar_email: false`) |
| **API** | `POST /api/robo/executar` body `{"modo_teste":false,"enviar_email":false}` (via proxy) ou `POST http://127.0.0.1:8003/robo/executar` no servidor |
| **CLI** | `cd /srv/finaud/tec/leiautes_bacen && ./run.sh` |

### Teste feito (2026-07-22)

| Item | Resultado |
|------|-----------|
| Disparo | `POST /robo/executar` com **`enviar_email=false`** |
| Execução | **id 13** · **sucesso** · ~95s |
| Contagens | 4 leiautes · 55 arquivos · 55 alterações (baseline após limpeza do banco — esperado) |
| E-mail | **0 enviados** (desabilitado de propósito) |
| Cron antigo | **confirmado ativo** em `tsala9334` e `paine6949` |

### O que Michel deve validar antes de desligar o antigo

1. Login / telas no site novo.
2. Execução na tela **Robô** (ou conferir log da execução 13 / próximas).
3. Uma rodada **com e-mail** só para `michel@finaud.com.br` (cron 18h ou API com `enviar_email: true`).
4. Comparar resultado com o legado na mesma janela (ambos às 18h Seg–Sex).
5. Só então desligar legado — ver Normativos `desligar_cron_servicos_antigos.md` (comentar linhas, não apagar).
