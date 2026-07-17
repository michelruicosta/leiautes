# -*- coding: utf-8 -*-
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

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
    excluir_usuario,
    listar_permissoes_perfis,
    listar_usuarios,
    obter_usuario,
    salvar_permissoes_perfis,
)
from persistencia.auditoria_db import registrar_log

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
        raise HTTPException(status_code=500, detail="Falha ao criar usuário")
    registrar_log(
        pagina="Usuários e perfis",
        acao="Criação",
        detalhe=f"Usuário {item['email']} criado com perfil {item['perfil_codigo']}.",
    )
    return UsuarioResumo(**item)


@router.put("/{usuario_id}", response_model=UsuarioResumo)
def atualizar(usuario_id: int, payload: UsuarioUpdateRequest) -> UsuarioResumo:
    antes = obter_usuario(usuario_id)
    item = atualizar_usuario(usuario_id, payload.model_dump(exclude_unset=True))
    if not item:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    acao = "Edição"
    if antes and antes["ativo"] and not item["ativo"]:
        acao = "Inativação"
    elif antes and not antes["ativo"] and item["ativo"]:
        acao = "Ativação"
    registrar_log(
        pagina="Usuários e perfis",
        acao=acao,
        detalhe=f"Usuário {item['email']} atualizado.",
    )
    return UsuarioResumo(**item)


@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def excluir(usuario_id: int) -> None:
    item = obter_usuario(usuario_id)
    if not item:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    if not excluir_usuario(usuario_id):
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    registrar_log(
        pagina="Usuários e perfis",
        acao="Exclusão",
        detalhe=f"Usuário {item['email']} excluído permanentemente.",
    )


@router.get("/perfis/permissoes", response_model=PermissoesPerfilResponse)
def obter_permissoes() -> PermissoesPerfilResponse:
    return PermissoesPerfilResponse(permissoes=listar_permissoes_perfis())


@router.put("/perfis/permissoes", response_model=PermissoesPerfilResponse)
def salvar_permissoes(
    payload: PermissoesPerfilUpdateRequest,
) -> PermissoesPerfilResponse:
    registrar_log(
        pagina="Usuários e perfis",
        acao="Edição",
        detalhe="Permissões dos perfis atualizadas.",
    )
    return PermissoesPerfilResponse(
        permissoes=salvar_permissoes_perfis(payload.permissoes)
    )
