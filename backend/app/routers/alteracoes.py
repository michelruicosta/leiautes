# -*- coding: utf-8 -*-
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import AlteracaoListaResponse, AlteracaoResumo
from persistencia.alteracoes_db import listar_alteracoes, obter_alteracao

router = APIRouter(prefix="/alteracoes", tags=["alteracoes"])


@router.get("", response_model=AlteracaoListaResponse)
def listar(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    status: str | None = None,
    leiaute_codigo: str | None = None,
) -> AlteracaoListaResponse:
    itens, total = listar_alteracoes(
        limit=limit,
        offset=offset,
        status=status,
        leiaute_codigo=leiaute_codigo,
    )
    return AlteracaoListaResponse(
        total=total,
        limit=limit,
        offset=offset,
        alteracoes=[AlteracaoResumo(**item) for item in itens],
    )


@router.get("/{alteracao_id}", response_model=AlteracaoResumo)
def obter(alteracao_id: int) -> AlteracaoResumo:
    item = obter_alteracao(alteracao_id)
    if not item:
        raise HTTPException(status_code=404, detail="Alteracao nao encontrada")
    return AlteracaoResumo(**item)
