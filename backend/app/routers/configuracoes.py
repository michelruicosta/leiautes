# -*- coding: utf-8 -*-
from __future__ import annotations

from fastapi import APIRouter

from app.models.schemas import ConfiguracoesResponse, ConfiguracoesUpdateRequest
from persistencia.config_db import listar_configuracoes, salvar_configuracoes

router = APIRouter(prefix="/configuracoes", tags=["configuracoes"])


@router.get("", response_model=ConfiguracoesResponse)
def obter_configuracoes() -> ConfiguracoesResponse:
    return ConfiguracoesResponse(configuracoes=listar_configuracoes())


@router.put("", response_model=ConfiguracoesResponse)
def atualizar_configuracoes(
    payload: ConfiguracoesUpdateRequest,
) -> ConfiguracoesResponse:
    return ConfiguracoesResponse(
        configuracoes=salvar_configuracoes(payload.configuracoes)
    )
