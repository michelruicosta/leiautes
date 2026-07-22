# -*- coding: utf-8 -*-
from __future__ import annotations

from fastapi import APIRouter, Query

from app.models.schemas import LogAuditoriaItem, LogAuditoriaListaResponse
from persistencia.auditoria_db import listar_logs

router = APIRouter(prefix="/auditoria", tags=["auditoria"])


@router.get("", response_model=LogAuditoriaListaResponse)
def listar_log_auditoria(
    data_de: str | None = Query(default=None),
    data_ate: str | None = Query(default=None),
    pagina: str | None = Query(default=None),
    acao: str | None = Query(default=None),
    usuario: str | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> LogAuditoriaListaResponse:
    itens, total = listar_logs(
        data_de=data_de,
        data_ate=data_ate,
        pagina=pagina,
        acao=acao,
        usuario=usuario,
        limit=limit,
        offset=offset,
    )
    return LogAuditoriaListaResponse(
        total=total,
        registros=[LogAuditoriaItem(**item) for item in itens],
    )
