# -*- coding: utf-8 -*-
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    PermissoesPerfilResponse,
    PermissoesPerfilUpdateRequest,
    UsuarioCreateRequest,
    UsuarioListaResponse,
    UsuarioResumo,
    UsuarioUpdateRequest,
)
from persistencia.usuarios_db import (
    atualizar_usuario,
    criar_usuario,
    listar_permissoes_perfis,
    listar_usuarios,
    obter_usuario,
    salvar_permissoes_perfis,
)

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


@router.get("", response_model=UsuarioListaResponse)
def listar() -> UsuarioListaResponse:
    itens, total = listar_usuarios()
    return UsuarioListaResponse(
        total=total,
        usuarios=[UsuarioResumo(**item) for item in itens],
    )


@router.post("", response_model=UsuarioResumo)
def criar(payload: UsuarioCreateRequest) -> UsuarioResumo:
    usuario_id = criar_usuario(payload.model_dump())
    item = obter_usuario(usuario_id)
    if not item:
        raise HTTPException(status_code=500, detail="Falha ao criar usuario")
    return UsuarioResumo(**item)


@router.put("/{usuario_id}", response_model=UsuarioResumo)
def atualizar(usuario_id: int, payload: UsuarioUpdateRequest) -> UsuarioResumo:
    item = atualizar_usuario(usuario_id, payload.model_dump(exclude_unset=True))
    if not item:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")
    return UsuarioResumo(**item)


@router.get("/perfis/permissoes", response_model=PermissoesPerfilResponse)
def obter_permissoes() -> PermissoesPerfilResponse:
    return PermissoesPerfilResponse(permissoes=listar_permissoes_perfis())


@router.put("/perfis/permissoes", response_model=PermissoesPerfilResponse)
def salvar_permissoes(
    payload: PermissoesPerfilUpdateRequest,
) -> PermissoesPerfilResponse:
    return PermissoesPerfilResponse(
        permissoes=salvar_permissoes_perfis(payload.permissoes)
    )
