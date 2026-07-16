# -*- coding: utf-8 -*-
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import ExecucaoListaResponse, ExecucaoResumo
from persistencia.execucoes_db import listar_execucoes, obter_ultima_execucao

router = APIRouter(prefix="/execucoes", tags=["execucoes"])


@router.get("/ultima", response_model=ExecucaoResumo)
def ultima_execucao() -> ExecucaoResumo:
    row = obter_ultima_execucao()
    if not row:
        raise HTTPException(status_code=404, detail="Nenhuma execucao registrada")
    return ExecucaoResumo(**row)


@router.get("", response_model=ExecucaoListaResponse)
def listar(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> ExecucaoListaResponse:
    itens, total = listar_execucoes(limit=limit, offset=offset)
    return ExecucaoListaResponse(
        total=total,
        execucoes=[ExecucaoResumo(**item) for item in itens],
    )
