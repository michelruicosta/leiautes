# -*- coding: utf-8 -*-
from __future__ import annotations

import json

from fastapi import APIRouter

from app.models.schemas import AlteracaoResumo, DashboardResponse, ExecucaoResumo
from persistencia.execucoes_db import resumo_dashboard

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _json_list(valor: str | None) -> list[str]:
    if not valor:
        return []
    try:
        parsed = json.loads(valor)
        return parsed if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        return []


@router.get("", response_model=DashboardResponse)
def obter_dashboard() -> DashboardResponse:
    data = resumo_dashboard()
    ultima = data.get("ultima_execucao")
    recentes = []
    for row in data.get("alteracoes_recentes", []):
        recentes.append(
            AlteracaoResumo(
                **{
                    **row,
                    "itens_incluidos": _json_list(row.get("itens_incluidos")),
                    "itens_removidos": _json_list(row.get("itens_removidos")),
                    "itens_alterados": _json_list(row.get("itens_alterados")),
                }
            )
        )
    return DashboardResponse(
        ultima_execucao=ExecucaoResumo(**ultima) if ultima else None,
        qtd_leiautes=data["qtd_leiautes"],
        qtd_arquivos=data["qtd_arquivos"],
        qtd_alteracoes=data["qtd_alteracoes"],
        alteracoes_recentes=recentes,
    )
