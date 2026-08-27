# -*- coding: utf-8 -*-
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.deps.auth import exigir_rota
from app.models.schemas import (
    LeiauteCreateRequest,
    LeiauteListaResponse,
    LeiauteResumo,
    LeiauteUpdateRequest,
)
from persistencia.leiautes_db import (
    atualizar_leiaute,
    criar_leiaute,
    excluir_leiaute,
    listar_leiautes,
    obter_leiaute,
)
from persistencia.auditoria_db import registrar_log

router = APIRouter(
    prefix="/leiautes",
    tags=["leiautes"],
    dependencies=[Depends(exigir_rota("admin-leiautes"))],
)


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
    registrar_log(
        pagina="Cadastro de Leiautes",
        acao="Criação",
        detalhe=f"Leiaute {item['codigo']} criado.",
    )
    return LeiauteResumo(**item)


@router.put("/{leiaute_id}", response_model=LeiauteResumo)
def atualizar(leiaute_id: int, payload: LeiauteUpdateRequest) -> LeiauteResumo:
    antes = obter_leiaute(leiaute_id)
    item = atualizar_leiaute(leiaute_id, payload.model_dump(exclude_unset=True))
    if not item:
        raise HTTPException(status_code=404, detail="Leiaute não encontrado")
    acao = "Edição"
    if antes and antes["ativo"] and not item["ativo"]:
        acao = "Inativação"
    elif antes and not antes["ativo"] and item["ativo"]:
        acao = "Ativação"
    registrar_log(
        pagina="Cadastro de Leiautes",
        acao=acao,
        detalhe=f"Leiaute {item['codigo']} atualizado.",
    )
    return LeiauteResumo(**item)


@router.delete("/{leiaute_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def excluir(leiaute_id: int) -> None:
    item = obter_leiaute(leiaute_id)
    if not item:
        raise HTTPException(status_code=404, detail="Leiaute não encontrado")
    ok = excluir_leiaute(leiaute_id)
    if not ok:
        raise HTTPException(
            status_code=409,
            detail=(
                "Não foi possível excluir este leiaute porque há arquivos ou histórico vinculados. "
                "Use Inativar para removê-lo do monitoramento."
            ),
        )
    registrar_log(
        pagina="Cadastro de Leiautes",
        acao="Exclusão",
        detalhe=f"Leiaute {item['codigo']} excluído permanentemente.",
    )
