# -*- coding: utf-8 -*-
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import (
    LeiauteCreateRequest,
    LeiauteListaResponse,
    LeiauteResumo,
    LeiauteUpdateRequest,
)
from persistencia.leiautes_db import (
    atualizar_leiaute,
    criar_leiaute,
    listar_leiautes,
    obter_leiaute,
)

router = APIRouter(prefix="/leiautes", tags=["leiautes"])


@router.get("", response_model=LeiauteListaResponse)
def listar(ativos: bool | None = Query(default=None)) -> LeiauteListaResponse:
    itens, total = listar_leiautes(ativos=ativos)
    return LeiauteListaResponse(
        total=total,
        leiautes=[LeiauteResumo(**item) for item in itens],
    )


@router.get("/{leiaute_id}", response_model=LeiauteResumo)
def obter(leiaute_id: int) -> LeiauteResumo:
    item = obter_leiaute(leiaute_id)
    if not item:
        raise HTTPException(status_code=404, detail="Leiaute não encontrado")
    return LeiauteResumo(**item)


@router.post("", response_model=LeiauteResumo)
def criar(payload: LeiauteCreateRequest) -> LeiauteResumo:
    leiaute_id = criar_leiaute(payload.model_dump())
    item = obter_leiaute(leiaute_id)
    if not item:
        raise HTTPException(status_code=500, detail="Falha ao criar leiaute")
    return LeiauteResumo(**item)


@router.put("/{leiaute_id}", response_model=LeiauteResumo)
def atualizar(leiaute_id: int, payload: LeiauteUpdateRequest) -> LeiauteResumo:
    item = atualizar_leiaute(leiaute_id, payload.model_dump(exclude_unset=True))
    if not item:
        raise HTTPException(status_code=404, detail="Leiaute não encontrado")
    return LeiauteResumo(**item)
