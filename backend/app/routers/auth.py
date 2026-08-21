# -*- coding: utf-8 -*-
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app import config
from app.deps.auth import exigir_usuario
from app.models.schemas import (
    AlterarSenhaRequest,
    LoginRequest,
    LoginResponse,
    RecuperarSenhaRequest,
    UsuarioAuthResponse,
)
from app.services.auth_senha import validar_politica_senha
from app.services.auth_sessao import (
    emitir_token_sessao,
    hash_senha,
    tem_senha_local,
    verificar_senha,
)
from persistencia.auditoria_db import registrar_log
from persistencia.usuarios_db import (
    atualizar_senha_usuario,
    buscar_usuario_por_email,
    listar_permissoes_perfis,
)

router = APIRouter(prefix="/auth", tags=["auth"])

_ROTAS_ADMIN = [
    "dashboard",
    "leiautes",
    "alteracoes",
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


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, response: Response) -> LoginResponse:
    usuario = buscar_usuario_por_email(body.email)
    if usuario is None or not usuario.get("ativo"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos.",
        )
    if not tem_senha_local(usuario.get("senha_hash")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Este usuário foi liberado para entrar pelo portal Finaud. "
                "Ainda não há senha local definida neste app."
            ),
        )
    if not verificar_senha(body.senha, usuario.get("senha_hash")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos.",
        )
    token = emitir_token_sessao(usuario["id"])
    response.set_cookie(
        key=config.AUTH_COOKIE_NAME,
        value=token,
        max_age=config.AUTH_SESSAO_MAX_AGE_SEG,
        **_cookie_params(),
    )
    registrar_log(
        usuario=usuario["email"],
        pagina="Login",
        acao="Autenticação",
        detalhe="Login realizado com sucesso.",
    )
    return LoginResponse(usuario=_usuario_auth(usuario), mensagem="Login realizado.")


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def logout(response: Response) -> None:
    params = _cookie_params()
    response.delete_cookie(key=config.AUTH_COOKIE_NAME, **params)
    # SSO: ao sair do app, encerra também a sessão do portal neste domínio
    response.delete_cookie(key=config.PORTAL_COOKIE_NAME, **params)
    response.delete_cookie(key=config.AUDITORIA_PORTAL_COOKIE_NAME, **params)


@router.get("/me", response_model=UsuarioAuthResponse)
def me(usuario: dict = Depends(exigir_usuario)) -> UsuarioAuthResponse:
    return _usuario_auth(usuario)


@router.post("/recuperar-senha")
def recuperar_senha(body: RecuperarSenhaRequest) -> dict[str, str]:
    usuario = buscar_usuario_por_email(body.email)
    if usuario is not None and usuario.get("ativo"):
        registrar_log(
            usuario=usuario["email"],
            pagina="Login",
            acao="Recuperação de senha",
            detalhe="Solicitação de recuperação registrada. Envio de e-mail será integrado ao SMTP.",
        )
    return {
        "mensagem": (
            "Se o e-mail estiver ativo, a recuperação será encaminhada. "
            "Nesta fase, peça ao administrador para definir uma senha temporária."
        )
    }


@router.post("/alterar-senha")
def alterar_senha(
    body: AlterarSenhaRequest,
    usuario: dict = Depends(exigir_usuario),
) -> dict[str, str]:
    if body.nova_senha != body.confirmar_senha:
        raise HTTPException(status_code=400, detail="As senhas não coincidem.")
    if body.senha_atual == body.nova_senha:
        raise HTTPException(
            status_code=400,
            detail="A nova senha deve ser diferente da senha atual.",
        )
    erro = validar_politica_senha(body.nova_senha)
    if erro:
        raise HTTPException(status_code=400, detail=erro)
    if not tem_senha_local(usuario.get("senha_hash")):
        raise HTTPException(
            status_code=400,
            detail="Este usuário ainda não tem senha local definida.",
        )
    if not verificar_senha(body.senha_atual, usuario.get("senha_hash")):
        raise HTTPException(status_code=400, detail="Senha atual incorreta.")
    atualizar_senha_usuario(usuario["id"], hash_senha(body.nova_senha))
    registrar_log(
        usuario=usuario["email"],
        pagina="Alterar senha",
        acao="Alterar senha",
        detalhe="Senha alterada pelo usuário.",
    )
    return {"mensagem": "Senha alterada com sucesso."}
