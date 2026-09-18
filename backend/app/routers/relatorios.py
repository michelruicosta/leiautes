# -*- coding: utf-8 -*-
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from app.deps.auth import exigir_rota
from app.services.relatorio_excel import gerar_relatorio_alteracoes_xlsx

# Relatório é baixado na tela Alterações — mesma permissão.
router = APIRouter(
    prefix="/relatorios",
    tags=["relatorios"],
    dependencies=[Depends(exigir_rota("alteracoes"))],
)


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
