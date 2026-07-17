# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from app.config import RAIZ_PROJETO
from app.models.schemas import ExecucaoListaResponse, ExecucaoLogResponse, ExecucaoResumo
from persistencia.execucoes_db import listar_execucoes, obter_execucao, obter_ultima_execucao

router = APIRouter(prefix="/execucoes", tags=["execucoes"])


def _ler_log_execucao(log_path: str | None, fallback: str | None) -> tuple[str, bool]:
    if not log_path:
        return (fallback or "Log técnico não localizado para esta execução.", False)

    caminho = Path(log_path)
    if not caminho.is_absolute():
        caminho = RAIZ_PROJETO / caminho
    try:
        resolvido = caminho.resolve()
    except OSError:
        return (fallback or f"Arquivo de log inválido: {log_path}", False)

    raiz = RAIZ_PROJETO.resolve()
    if raiz not in resolvido.parents and resolvido != raiz:
        return (fallback or f"Log fora da pasta do projeto: {log_path}", False)
    if not resolvido.exists():
        return (fallback or f"Arquivo de log não encontrado: {log_path}", False)

    texto = resolvido.read_text(encoding="utf-8", errors="replace")
    return (texto[-20000:] if len(texto) > 20000 else texto, True)


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


@router.get("/{execucao_id}/log", response_model=ExecucaoLogResponse)
def obter_log(execucao_id: int) -> ExecucaoLogResponse:
    row = obter_execucao(execucao_id)
    if not row:
        raise HTTPException(status_code=404, detail="Execucao nao encontrada")
    texto, disponivel = _ler_log_execucao(row.get("log_path"), row.get("erro"))
    return ExecucaoLogResponse(
        execucao=ExecucaoResumo(**row),
        log_texto=texto,
        log_path=row.get("log_path"),
        disponivel=disponivel,
    )
