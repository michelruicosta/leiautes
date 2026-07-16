# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    version: str


class LeiauteResumo(BaseModel):
    id: int
    codigo: str
    nome: str
    categoria: str
    url_bacen: str
    ativo: bool = True
    ultima_leitura_em: Optional[str] = None


class LeiauteListaResponse(BaseModel):
    total: int
    leiautes: list[LeiauteResumo]


class ExecucaoResumo(BaseModel):
    id: int
    iniciado_em: str
    finalizado_em: Optional[str] = None
    status: str
    qtd_leiautes: int = 0
    qtd_arquivos: int = 0
    qtd_alteracoes: int = 0
    emails_enviados: int = 0
    erro: Optional[str] = None
    log_path: Optional[str] = None


class ExecucaoListaResponse(BaseModel):
    total: int
    execucoes: list[ExecucaoResumo]


class AlteracaoResumo(BaseModel):
    id: int
    execucao_id: int
    leiaute_codigo: str
    arquivo_nome: str
    arquivo_tipo: str
    resumo_executivo: str = ""
    impacto_sugerido: str = ""
    status: str = "pendente"
    criado_em: str
    itens_incluidos: list[str] = Field(default_factory=list)
    itens_removidos: list[str] = Field(default_factory=list)
    itens_alterados: list[str] = Field(default_factory=list)


class AlteracaoListaResponse(BaseModel):
    total: int
    alteracoes: list[AlteracaoResumo]
