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

AUTH_SECRET_KEY = os.environ.get(
    "AUTH_SECRET_KEY",
    "dev-alterar-em-producao-leiautes-bacen",
)
AUTH_COOKIE_NAME = "leiautes_sessao"
AUTH_SESSAO_MAX_AGE_SEG = 60 * 60 * 24 * 7
AUTH_SEED_PASSWORD = os.environ.get("AUTH_SEED_PASSWORD", "finaud-dev-2026")
AUTH_COOKIE_DOMAIN = os.environ.get("AUTH_COOKIE_DOMAIN") or None
_cookie_secure_env = os.environ.get("AUTH_COOKIE_SECURE")
if _cookie_secure_env is not None:
    AUTH_COOKIE_SECURE = _cookie_secure_env.strip().lower() in ("1", "true", "yes")
else:
    AUTH_COOKIE_SECURE = bool(AUTH_COOKIE_DOMAIN)

URL_LOGIN_RECUPERACAO = os.environ.get(
    "LEIAUTES_FRONTEND_URL",
    "http://localhost:5175",
).rstrip("/")

PORTAL_AUTH_URL = os.environ.get(
    "PORTAL_AUTH_URL",
    "http://127.0.0.1:8002",
).rstrip("/")
PORTAL_COOKIE_NAME = os.environ.get("PORTAL_COOKIE_NAME", "finaud_portal_sessao")
PORTAL_AUTH_TIMEOUT_SEG = float(os.environ.get("PORTAL_AUTH_TIMEOUT_SEG", "5"))
PORTAL_URL = os.environ.get("PORTAL_URL", "https://finaudapps.com.br").rstrip("/")
