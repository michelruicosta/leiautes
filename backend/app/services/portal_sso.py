# -*- coding: utf-8 -*-
"""SSO — confia no login do portal Finaud (cookie compartilhado)."""
from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from dataclasses import dataclass

from app import config

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UsuarioPortal:
    email: str
    nome: str
    perfil_codigo: str


def consultar_usuario_portal(
    cookie_valor: str,
    *,
    cookie_name: str,
    auth_base_url: str | None = None,
) -> UsuarioPortal | None:
    """
    Pergunta à API do portal quem está logado (GET /auth/me com o cookie).
    Retorna None se sessão inválida ou portal inacessível.
    """
    base = (auth_base_url or config.PORTAL_AUTH_URL or "").rstrip("/")
    if not base or not cookie_valor:
        return None
    url = f"{base}/auth/me"
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "Cookie": f"{cookie_name}={cookie_valor}",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=config.PORTAL_AUTH_TIMEOUT_SEG) as resp:
            if resp.status != 200:
                return None
            data = json.loads(resp.read().decode("utf-8"))
    except (
        urllib.error.URLError,
        urllib.error.HTTPError,
        TimeoutError,
        json.JSONDecodeError,
        ValueError,
    ) as exc:
        logger.info("SSO portal indisponivel ou sessao invalida (%s): %s", cookie_name, exc)
        return None

    email = str(data.get("email") or "").strip()
    if not email:
        return None
    return UsuarioPortal(
        email=email,
        nome=str(data.get("nome") or email),
        perfil_codigo=str(data.get("perfil_codigo") or "operador"),
    )
