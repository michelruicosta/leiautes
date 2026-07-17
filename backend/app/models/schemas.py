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
    tipos_arquivo: list[str] = Field(default_factory=list)
    ativo: bool = True
    ultima_leitura_em: Optional[str] = None


class LeiauteListaResponse(BaseModel):
    total: int
    leiautes: list[LeiauteResumo]


class LeiauteCreateRequest(BaseModel):
    codigo: str = Field(min_length=2, max_length=40)
    nome: str = Field(min_length=2, max_length=160)
    categoria: str = Field(min_length=2, max_length=40)
    url_bacen: str = Field(min_length=10, max_length=500)
    tipos_arquivo: list[str] = Field(default_factory=list)
    ativo: bool = True


class LeiauteUpdateRequest(BaseModel):
    codigo: Optional[str] = Field(default=None, min_length=2, max_length=40)
    nome: Optional[str] = Field(default=None, min_length=2, max_length=160)
    categoria: Optional[str] = Field(default=None, min_length=2, max_length=40)
    url_bacen: Optional[str] = Field(default=None, min_length=10, max_length=500)
    tipos_arquivo: Optional[list[str]] = None
    ativo: Optional[bool] = None


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


class ExecucaoLogResponse(BaseModel):
    execucao: ExecucaoResumo
    log_texto: str = ""
    log_path: Optional[str] = None
    disponivel: bool = False


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
    limit: int = 50
    offset: int = 0
    alteracoes: list[AlteracaoResumo]


class DashboardResponse(BaseModel):
    ultima_execucao: Optional[ExecucaoResumo] = None
    qtd_leiautes: int = 0
    qtd_arquivos: int = 0
    qtd_alteracoes: int = 0
    alteracoes_recentes: list[AlteracaoResumo] = Field(default_factory=list)


class ConfiguracoesResponse(BaseModel):
    configuracoes: dict


class ConfiguracoesUpdateRequest(BaseModel):
    configuracoes: dict


class RoboStatusResponse(BaseModel):
    script_motor: str
    script_existe: bool
    ultima_execucao: Optional[ExecucaoResumo] = None


class RoboExecutarRequest(BaseModel):
    modo_teste: bool = False
    enviar_email: bool = False
    data_teste: Optional[str] = Field(default=None, max_length=10)
    timeout_segundos: int = Field(default=900, ge=30, le=7200)


class RoboExecutarResponse(BaseModel):
    execucao_id: int
    status: str
    returncode: int
    stdout_tail: str = ""
    stderr_tail: str = ""


class UsuarioResumo(BaseModel):
    id: int
    email: str
    nome: str
    perfil_codigo: str
    cargo: Optional[str] = None
    departamento: Optional[str] = None
    ativo: bool = True


class UsuarioListaResponse(BaseModel):
    total: int
    usuarios: list[UsuarioResumo]


class UsuarioCreateRequest(BaseModel):
    email: str = Field(min_length=3, max_length=200)
    nome: str = Field(min_length=2, max_length=120)
    perfil_codigo: str = Field(pattern=r"^(operador|gestor|administrador)$")
    cargo: Optional[str] = Field(default=None, max_length=80)
    departamento: Optional[str] = Field(default=None, max_length=80)
    ativo: bool = True


class UsuarioUpdateRequest(BaseModel):
    email: Optional[str] = Field(default=None, min_length=3, max_length=200)
    nome: Optional[str] = Field(default=None, min_length=2, max_length=120)
    perfil_codigo: Optional[str] = Field(
        default=None,
        pattern=r"^(operador|gestor|administrador)$",
    )
    cargo: Optional[str] = Field(default=None, max_length=80)
    departamento: Optional[str] = Field(default=None, max_length=80)
    ativo: Optional[bool] = None


class PermissoesPerfilResponse(BaseModel):
    permissoes: dict[str, list[str]]


class PermissoesPerfilUpdateRequest(BaseModel):
    permissoes: dict[str, list[str]]


class EmailGestorPreviewResponse(BaseModel):
    assunto: str
    destinatarios: list[str] = Field(default_factory=list)
    copia: list[str] = Field(default_factory=list)
    resumo: str
    alteracoes: list[AlteracaoResumo] = Field(default_factory=list)
    anexos: list[str] = Field(default_factory=list)
