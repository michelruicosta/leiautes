# -*- coding: utf-8 -*-
from __future__ import annotations

from fastapi import Cookie, Depends, HTTPException, status

from app import config
from app.services.auth_sessao import validar_token_sessao
from app.services.portal_sso import consultar_usuario_portal
from persistencia.usuarios_db import buscar_usuario_por_email, buscar_usuario_por_id


def _via_cookie_portal(cookie_valor: str, *, cookie_name: str, auth_base_url: str) -> dict | None:
    portal = consultar_usuario_portal(
        cookie_valor,
        cookie_name=cookie_name,
        auth_base_url=auth_base_url,
    )
    if portal is None:
        return None
    usuario = buscar_usuario_por_email(portal.email)
    if usuario is None or not usuario.get("ativo"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Seu usuário do portal não tem acesso ao Leiautes. "
                "Peça ao administrador para cadastrá-lo neste app."
            ),
        )
    return usuario


def _via_cookie_local(cookie_valor: str) -> dict | None:
    usuario_id = validar_token_sessao(cookie_valor)
    if usuario_id is None:
        return None
    usuario = buscar_usuario_por_id(usuario_id)
    if usuario is None or not usuario.get("ativo"):
        return None
    return usuario


def exigir_usuario(
    auditoria_sessao: str | None = Cookie(default=None, alias=config.AUDITORIA_PORTAL_COOKIE_NAME),
    finaud_portal_sessao: str | None = Cookie(default=None, alias=config.PORTAL_COOKIE_NAME),
    leiautes_sessao: str | None = Cookie(default=None, alias=config.AUTH_COOKIE_NAME),
) -> dict:
    # 1) Login via finaudapps.com.br/api → Auditoria (:8000)
    if auditoria_sessao:
        sessao = _via_cookie_portal(
            auditoria_sessao,
            cookie_name=config.AUDITORIA_PORTAL_COOKIE_NAME,
            auth_base_url=config.PORTAL_AUTH_URL,
        )
        if sessao is not None:
            return sessao
    # 2) Login legado via portal-auth (:8002)
    if finaud_portal_sessao:
        sessao = _via_cookie_portal(
            finaud_portal_sessao,
            cookie_name=config.PORTAL_COOKIE_NAME,
            auth_base_url=config.PORTAL_AUTH_LEGACY_URL,
        )
        if sessao is not None:
            return sessao
    # 3) Cookie próprio do Leiautes (login direto no app)
    if leiautes_sessao:
        sessao = _via_cookie_local(leiautes_sessao)
        if sessao is not None:
            return sessao

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Faça login para continuar.",
    )


def exigir_administrador(usuario: dict = Depends(exigir_usuario)) -> dict:
    if usuario.get("perfil_codigo") != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas administradores podem acessar esta área.",
        )
    return usuario
