# -*- coding: utf-8 -*-
from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status

from app import config
from app.deps.auth import exigir_usuario
from app.models.schemas import UsuarioAuthResponse
from persistencia.usuarios_db import listar_permissoes_perfis

router = APIRouter(prefix="/auth", tags=["auth"])

_ROTAS_ADMIN = [
    "dashboard",
    "alteracoes",
    "admin-leiautes",
    "admin-robo",
    "admin-configuracoes",
    "admin-usuarios",
    "admin-auditoria",
]


def _cookie_params() -> dict:
    params: dict = {"path": "/", "httponly": True, "samesite": "lax"}
    if config.AUTH_COOKIE_DOMAIN:
        params["domain"] = config.AUTH_COOKIE_DOMAIN
    if config.AUTH_COOKIE_SECURE:
        params["secure"] = True
    return params


def _rotas_do_perfil(perfil_codigo: str) -> list[str]:
    if perfil_codigo == "administrador":
        return list(_ROTAS_ADMIN)
    return list(listar_permissoes_perfis().get(perfil_codigo) or [])


def _usuario_auth(usuario: dict) -> UsuarioAuthResponse:
    return UsuarioAuthResponse(
        id=usuario["id"],
        email=usuario["email"],
        nome=usuario["nome"],
        perfil_codigo=usuario["perfil_codigo"],
        cargo=usuario.get("cargo"),
        departamento=usuario.get("departamento"),
        rotas_permitidas=_rotas_do_perfil(str(usuario.get("perfil_codigo") or "")),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def logout(response: Response) -> None:
    params = _cookie_params()
    # Apaga os três cookies SSO possíveis (limpeza de sessão anterior com login local)
    response.delete_cookie(key=config.AUTH_COOKIE_NAME, **params)
    response.delete_cookie(key=config.PORTAL_COOKIE_NAME, **params)
    response.delete_cookie(key=config.AUDITORIA_PORTAL_COOKIE_NAME, **params)


@router.get("/me", response_model=UsuarioAuthResponse)
def me(usuario: dict = Depends(exigir_usuario)) -> UsuarioAuthResponse:
    return _usuario_auth(usuario)
