# -*- coding: utf-8 -*-
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from app.models.schemas import VersaoArquivoListaResponse, VersaoArquivoResumo
from persistencia.versoes_db import listar_versoes, obter_caminho_download

router = APIRouter(prefix="/versoes", tags=["versoes"])


@router.get("", response_model=VersaoArquivoListaResponse)
def listar(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    leiaute_codigo: str | None = None,
    tipo: str | None = None,
    busca: str | None = None,
) -> VersaoArquivoListaResponse:
    itens, total = listar_versoes(
        limit=limit,
        offset=offset,
        leiaute_codigo=leiaute_codigo,
        tipo=tipo,
        busca=busca,
    )
    return VersaoArquivoListaResponse(
        total=total,
        limit=limit,
        offset=offset,
        versoes=[VersaoArquivoResumo(**item) for item in itens],
    )


@router.get("/{versao_id}/download")
def download(versao_id: int) -> FileResponse:
    resultado = obter_caminho_download(versao_id)
    if not resultado:
        raise HTTPException(status_code=404, detail="Versão não encontrada ou arquivo ausente")
    path, nome = resultado
    return FileResponse(
        path=path,
        filename=nome,
        media_type="application/octet-stream",
    )
