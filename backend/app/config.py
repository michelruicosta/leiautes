# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# backend/app/config.py -> raiz do repositorio
RAIZ_PROJETO = Path(__file__).resolve().parent.parent.parent
load_dotenv(RAIZ_PROJETO / ".env")

if str(RAIZ_PROJETO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROJETO))

API_VERSION = "0.1.0-mvp"
APP_NAME = "leiautes_bacen"

SCRIPT_MOTOR = RAIZ_PROJETO / "scripts" / "verifica_leiautes_finaud.py"
DB_PATH = Path(os.environ.get("LEIAUTES_DB_PATH", RAIZ_PROJETO / "dados" / "leiautes.db"))

# Ambiente: "production" desabilita /docs e /openapi.json (A01-9)
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development").strip().lower()

# Cookie de sessão local (mantido só para o logout limpar sessões antigas)
AUTH_COOKIE_NAME = "leiautes_sessao"
AUTH_COOKIE_DOMAIN = os.environ.get("AUTH_COOKIE_DOMAIN") or None
_cookie_secure_env = os.environ.get("AUTH_COOKIE_SECURE")
if _cookie_secure_env is not None:
    AUTH_COOKIE_SECURE = _cookie_secure_env.strip().lower() in ("1", "true", "yes")
else:
    AUTH_COOKIE_SECURE = bool(AUTH_COOKIE_DOMAIN)

# CORS — lista separada por vírgula no .env (A01-13)
# Em produção defina só as origens reais; o padrão inclui localhost para desenvolvimento.
_cors_env = os.environ.get("CORS_ALLOW_ORIGINS", "").strip()
if _cors_env:
    CORS_ALLOW_ORIGINS: list[str] = [o.strip() for o in _cors_env.split(",") if o.strip()]
else:
    CORS_ALLOW_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        "http://localhost:5176",
        "http://127.0.0.1:5176",
        "http://localhost:5177",
        "http://127.0.0.1:5177",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8001",
        "http://127.0.0.1:8002",
        "http://127.0.0.1:8003",
        "https://finaudapps.com.br",
        "https://www.finaudapps.com.br",
        "https://admin.finaudapps.com.br",
        "https://leiautes-bacen.finaudapps.com.br",
        "https://www.leiautes-bacen.finaudapps.com.br",
    ]

# SSO portal — ver documentacao/sso_portal_apps_finaud.md
PORTAL_AUTH_URL = os.environ.get(
    "PORTAL_AUTH_URL",
    "http://127.0.0.1:8000",
).rstrip("/")
PORTAL_AUTH_LEGACY_URL = os.environ.get(
    "PORTAL_AUTH_LEGACY_URL",
    "http://127.0.0.1:8002",
).rstrip("/")
AUDITORIA_PORTAL_COOKIE_NAME = os.environ.get(
    "AUDITORIA_PORTAL_COOKIE_NAME",
    "auditoria_sessao",
)
PORTAL_COOKIE_NAME = os.environ.get("PORTAL_COOKIE_NAME", "finaud_portal_sessao")
PORTAL_AUTH_TIMEOUT_SEG = float(os.environ.get("PORTAL_AUTH_TIMEOUT_SEG", "5"))
PORTAL_URL = os.environ.get("PORTAL_URL", "https://finaudapps.com.br").rstrip("/")
