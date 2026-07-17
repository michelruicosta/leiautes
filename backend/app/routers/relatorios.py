# -*- coding: utf-8 -*-
from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import Response

from app.services.relatorio_excel import gerar_relatorio_alteracoes_xlsx

router = APIRouter(prefix="/relatorios", tags=["relatorios"])


@router.get("/alteracoes.xlsx")
def exportar_alteracoes_xlsx(
    escopo: str = Query(default="historico", pattern="^(ultima|historico)$"),
) -> Response:
    conteudo, nome = gerar_relatorio_alteracoes_xlsx(escopo)
    return Response(
        content=conteudo,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{nome}"'},
    )
