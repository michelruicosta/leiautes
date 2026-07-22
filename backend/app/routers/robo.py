# -*- coding: utf-8 -*-
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    ExecucaoResumo,
    RoboExecutarRequest,
    RoboExecutarResponse,
    RoboStatusResponse,
)
from app.services.robo_leiautes import executar_robo_atual, status_robo
from persistencia.auditoria_db import registrar_log
from persistencia.execucoes_db import obter_ultima_execucao

router = APIRouter(prefix="/robo", tags=["robo"])


@router.get("/status", response_model=RoboStatusResponse)
def obter_status() -> RoboStatusResponse:
    status = status_robo()
    ultima = obter_ultima_execucao()
    return RoboStatusResponse(
        **status,
        ultima_execucao=ExecucaoResumo(**ultima) if ultima else None,
    )


@router.post("/executar", response_model=RoboExecutarResponse)
def executar(payload: RoboExecutarRequest) -> RoboExecutarResponse:
    try:
        resultado = executar_robo_atual(
            modo_teste=payload.modo_teste,
            enviar_email=payload.enviar_email,
            data_teste=payload.data_teste,
            timeout_segundos=payload.timeout_segundos,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    registrar_log(
        pagina="Robô",
        acao="Execução manual",
        detalhe=(
            f"Execução {resultado.execucao_id} finalizada com status {resultado.status} "
            f"(e-mail {'ativado' if payload.enviar_email else 'desativado'})."
        ),
    )
    return RoboExecutarResponse(**resultado.__dict__)
