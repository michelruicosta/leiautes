# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends

from app.deps.auth import exigir_rota
from app.models.schemas import AlteracaoResumo, EmailGestorPreviewResponse
from persistencia.alteracoes_db import listar_alteracoes
from persistencia.config_db import listar_configuracoes
from persistencia.usuarios_db import listar_emails_alerta

router = APIRouter(
    prefix="/email-gestor",
    tags=["email-gestor"],
    dependencies=[Depends(exigir_rota("email-gestor"))],
)


@router.get("/preview", response_model=EmailGestorPreviewResponse)
def preview_email() -> EmailGestorPreviewResponse:
    cfg = listar_configuracoes()
    alteracoes_raw, _ = listar_alteracoes(limit=20)
    alteracoes = [AlteracaoResumo(**item) for item in alteracoes_raw]
    hoje = datetime.now().strftime("%d/%m/%Y")
    assunto = str(
        cfg.get("email.assunto")
        or f"Atualização em leiautes Bacen - {hoje}"
    ).replace("{data}", hoje)
    if alteracoes:
        resumo = (
            f"Foram identificadas {len(alteracoes)} alteração(ões) nos leiautes "
            "monitorados. Consulte os itens abaixo antes de encaminhar ao gestor."
        )
    else:
        resumo = (
            "Nenhuma alteração de conteúdo foi registrada ainda. A prévia será "
            "preenchida automaticamente após o robô gravar diferenças no histórico."
        )
    return EmailGestorPreviewResponse(
        assunto=assunto,
        destinatarios=listar_emails_alerta(),
        copia=[],
        resumo=resumo,
        alteracoes=alteracoes,
        anexos=[item.arquivo_nome for item in alteracoes],
    )
