# -*- coding: utf-8 -*-
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.deps.auth import exigir_rota
from app.models.schemas import ConfiguracoesResponse, ConfiguracoesUpdateRequest
from persistencia.auditoria_db import registrar_log
from persistencia.config_db import listar_configuracoes, salvar_configuracoes

router = APIRouter(
    prefix="/configuracoes",
    tags=["configuracoes"],
    dependencies=[Depends(exigir_rota("admin-configuracoes"))],
)


@router.get("", response_model=ConfiguracoesResponse)
def obter_configuracoes() -> ConfiguracoesResponse:
    return ConfiguracoesResponse(configuracoes=listar_configuracoes())


@router.put("", response_model=ConfiguracoesResponse)
def atualizar_configuracoes(
    payload: ConfiguracoesUpdateRequest,
) -> ConfiguracoesResponse:
    configuracoes = salvar_configuracoes(payload.configuracoes)
    registrar_log(
        pagina="Configurações",
        acao="Edição",
        detalhe=f"{len(payload.configuracoes)} parâmetro(s) atualizado(s).",
    )
    return ConfiguracoesResponse(configuracoes=configuracoes)
