# -*- coding: utf-8 -*-
from __future__ import annotations

from fastapi import Cookie, Depends, HTTPException, status

from app import config
from app.services.auth_sessao import validar_token_sessao
from persistencia.usuarios_db import buscar_usuario_por_id


def exigir_usuario(
    leiautes_sessao: str | None = Cookie(
        default=None,
        alias=config.AUTH_COOKIE_NAME,
    ),
) -> dict:
    if not leiautes_sessao:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Faça login para continuar.",
        )
    usuario_id = validar_token_sessao(leiautes_sessao)
    if usuario_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Faça login para continuar.",
        )
    usuario = buscar_usuario_por_id(usuario_id)
    if usuario is None or not usuario.get("ativo"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Faça login para continuar.",
        )
    return usuario
