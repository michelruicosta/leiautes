# -*- coding: utf-8 -*-
"""SQLite - leiautes, execucoes e historico do robo."""
from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

RAIZ = Path(__file__).resolve().parent.parent


def get_db_path() -> Path:
    custom = os.getenv("LEIAUTES_DB_PATH", "").strip()
    if custom:
        return Path(custom)
    return RAIZ / "dados" / "leiautes.db"


def _connect() -> sqlite3.Connection:
    path = get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def conectar() -> sqlite3.Connection:
    return _connect()


def _agora() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS configuracoes (
                chave TEXT PRIMARY KEY,
                valor TEXT NOT NULL,
                atualizado_em TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                nome TEXT NOT NULL,
                perfil_codigo TEXT NOT NULL DEFAULT 'operador',
                senha_hash TEXT,
                cargo TEXT,
                departamento TEXT,
                ativo INTEGER NOT NULL DEFAULT 1,
                criado_em TEXT NOT NULL,
                atualizado_em TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS perfis_permissoes (
                perfil_codigo TEXT PRIMARY KEY,
                rotas_permitidas TEXT NOT NULL DEFAULT '[]',
                atualizado_em TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS leiautes_monitorados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT NOT NULL UNIQUE,
                nome TEXT NOT NULL,
                categoria TEXT NOT NULL,
                url_bacen TEXT NOT NULL,
                tipos_arquivo TEXT NOT NULL DEFAULT '[]',
                ativo INTEGER NOT NULL DEFAULT 1,
                ultima_leitura_em TEXT,
                criado_em TEXT NOT NULL,
                atualizado_em TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS execucoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                iniciado_em TEXT NOT NULL,
                finalizado_em TEXT,
                status TEXT NOT NULL DEFAULT 'em_andamento',
                qtd_leiautes INTEGER NOT NULL DEFAULT 0,
                qtd_arquivos INTEGER NOT NULL DEFAULT 0,
                qtd_alteracoes INTEGER NOT NULL DEFAULT 0,
                emails_enviados INTEGER NOT NULL DEFAULT 0,
                erro TEXT,
                log_path TEXT
            );

            CREATE TABLE IF NOT EXISTS arquivos_monitorados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                leiaute_id INTEGER,
                url TEXT NOT NULL UNIQUE,
                nome_arquivo TEXT NOT NULL,
                tipo_arquivo TEXT NOT NULL,
                etag TEXT,
                last_modified TEXT,
                content_length TEXT,
                final_url TEXT,
                partial_fp TEXT,
                hash_conteudo TEXT,
                ultima_versao_id INTEGER,
                ultima_verificacao_em TEXT,
                criado_em TEXT NOT NULL,
                atualizado_em TEXT NOT NULL,
                FOREIGN KEY (leiaute_id) REFERENCES leiautes_monitorados(id)
            );

            CREATE TABLE IF NOT EXISTS versoes_arquivos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                arquivo_id INTEGER NOT NULL,
                execucao_id INTEGER,
                caminho_arquivo TEXT,
                caminho_texto TEXT,
                hash_conteudo TEXT,
                tamanho_bytes INTEGER,
                metadados TEXT NOT NULL DEFAULT '{}',
                criado_em TEXT NOT NULL,
                FOREIGN KEY (arquivo_id) REFERENCES arquivos_monitorados(id),
                FOREIGN KEY (execucao_id) REFERENCES execucoes(id)
            );

            CREATE TABLE IF NOT EXISTS alteracoes_detectadas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                execucao_id INTEGER NOT NULL,
                arquivo_id INTEGER NOT NULL,
                versao_anterior_id INTEGER,
                versao_atual_id INTEGER,
                resumo_executivo TEXT NOT NULL DEFAULT '',
                impacto_sugerido TEXT NOT NULL DEFAULT '',
                itens_incluidos TEXT NOT NULL DEFAULT '[]',
                itens_removidos TEXT NOT NULL DEFAULT '[]',
                itens_alterados TEXT NOT NULL DEFAULT '[]',
                status TEXT NOT NULL DEFAULT 'pendente',
                criado_em TEXT NOT NULL,
                FOREIGN KEY (execucao_id) REFERENCES execucoes(id),
                FOREIGN KEY (arquivo_id) REFERENCES arquivos_monitorados(id),
                FOREIGN KEY (versao_anterior_id) REFERENCES versoes_arquivos(id),
                FOREIGN KEY (versao_atual_id) REFERENCES versoes_arquivos(id)
            );

            CREATE TABLE IF NOT EXISTS emails_enviados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                execucao_id INTEGER,
                assunto TEXT NOT NULL,
                destinatarios TEXT NOT NULL DEFAULT '[]',
                corpo_html TEXT,
                status TEXT NOT NULL,
                erro TEXT,
                enviado_em TEXT NOT NULL,
                FOREIGN KEY (execucao_id) REFERENCES execucoes(id)
            );

            CREATE TABLE IF NOT EXISTS auditoria (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT NOT NULL DEFAULT 'sistema',
                pagina TEXT NOT NULL,
                acao TEXT NOT NULL,
                detalhe TEXT NOT NULL DEFAULT '',
                criado_em TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_execucoes_inicio
                ON execucoes(iniciado_em);
            CREATE INDEX IF NOT EXISTS idx_alteracoes_execucao
                ON alteracoes_detectadas(execucao_id);
            CREATE INDEX IF NOT EXISTS idx_arquivos_leiaute
                ON arquivos_monitorados(leiaute_id);
            """
        )
    seed_configuracoes_padrao()
    seed_perfis_padrao()
    seed_leiautes_padrao()


def seed_configuracoes_padrao() -> None:
    defaults = {
        "empresa.nome": "FINAUD TEC",
        "empresa.cor_marca": "#3333a8",
        "empresa.subtitulo": "Leiautes Bacen - Monitoramento",
        "email.enviar_sem_alteracao": False,
        "email.anexar_alterados": True,
        "monitor.connect_timeout": 10,
        "monitor.read_timeout": 10,
        "monitor.only_atual": True,
        "monitor.quiet_baseline": True,
        "monitor.exclude_patterns": ["versoes_anteriores", "anteriores", "historico"],
        "anexos.max_attachments": 8,
        "anexos.max_single_mb": 4,
        "anexos.max_total_mb": 18,
        "anexos.extensoes": ["pdf", "xls", "xlsx", "xsd", "zip"],
        "comparacao.nivel_resumo": "executivo_tecnico",
        "comparacao.max_diferencas_email": 12,
    }
    agora = _agora()
    with _connect() as conn:
        for chave, valor in defaults.items():
            conn.execute(
                """
                INSERT OR IGNORE INTO configuracoes (chave, valor, atualizado_em)
                VALUES (?, ?, ?)
                """,
                (chave, _json(valor), agora),
            )


def seed_leiautes_padrao() -> None:
    leiautes = [
        (
            "DDR-2011",
            "DDR - Documento 2011",
            "DDR",
            "https://www.bcb.gov.br/estabilidadefinanceira/leiautedocumentoDDR2011",
            ["pdf", "xsd", "zip", "xls", "xlsx"],
        ),
        (
            "DRM-2060",
            "DRM - Documento 2060",
            "DRM",
            "https://www.bcb.gov.br/estabilidadefinanceira/leiautedocumentoDRM",
            ["pdf", "xsd", "zip", "xls", "xlsx"],
        ),
        (
            "DLO-2061",
            "DLO - Documento 2061",
            "DLO",
            "https://www.bcb.gov.br/estabilidadefinanceira/leiautedoc2061",
            ["pdf", "xsd", "zip", "xls", "xlsx"],
        ),
        (
            "DLI-2062",
            "DLI - Documento 2062",
            "DLI",
            "https://www.bcb.gov.br/estabilidadefinanceira/leiautedoc2062",
            ["pdf", "xsd", "zip", "xls", "xlsx"],
        ),
        (
            "DRL-2160",
            "DRL - Documento 2160",
            "DRL",
            "https://www.bcb.gov.br/estabilidadefinanceira/leiaute_drl2160",
            ["pdf", "xsd", "zip", "xls", "xlsx"],
        ),
        (
            "SCD-4111",
            "SCD - Documento 4111",
            "SCD",
            "https://www.bcb.gov.br/estabilidadefinanceira/leiautedocumentoscrd",
            ["pdf", "xsd"],
        ),
    ]
    agora = _agora()
    with _connect() as conn:
        for codigo, nome, categoria, url, tipos in leiautes:
            conn.execute(
                """
                INSERT OR IGNORE INTO leiautes_monitorados (
                    codigo, nome, categoria, url_bacen, tipos_arquivo,
                    ativo, criado_em, atualizado_em
                ) VALUES (?, ?, ?, ?, ?, 1, ?, ?)
                """,
                (codigo, nome, categoria, url, _json(tipos), agora, agora),
            )


def seed_perfis_padrao() -> None:
    permissoes = {
        "operador": ["dashboard", "leiautes", "alteracoes", "admin-robo"],
        "gestor": ["dashboard", "leiautes", "alteracoes", "email-gestor"],
        "administrador": [
            "dashboard",
            "leiautes",
            "alteracoes",
            "email-gestor",
            "admin-robo",
            "admin-configuracoes",
            "admin-usuarios",
        ],
    }
    agora = _agora()
    with _connect() as conn:
        for perfil, rotas in permissoes.items():
            conn.execute(
                """
                INSERT OR IGNORE INTO perfis_permissoes (
                    perfil_codigo, rotas_permitidas, atualizado_em
                ) VALUES (?, ?, ?)
                """,
                (perfil, _json(rotas), agora),
            )


def iniciar_execucao(log_path: Optional[str] = None) -> int:
    init_db()
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO execucoes (iniciado_em, status, log_path)
            VALUES (?, 'em_andamento', ?)
            """,
            (_agora(), log_path),
        )
        return int(cur.lastrowid)


def definir_log_execucao(execucao_id: int, log_path: Optional[str]) -> None:
    with _connect() as conn:
        conn.execute(
            """
            UPDATE execucoes
            SET log_path = ?
            WHERE id = ?
            """,
            (log_path, execucao_id),
        )


def finalizar_execucao(
    execucao_id: int,
    *,
    status: str,
    qtd_leiautes: int = 0,
    qtd_arquivos: int = 0,
    qtd_alteracoes: int = 0,
    emails_enviados: int = 0,
    erro: Optional[str] = None,
) -> None:
    with _connect() as conn:
        conn.execute(
            """
            UPDATE execucoes
            SET finalizado_em = ?, status = ?, qtd_leiautes = ?,
                qtd_arquivos = ?, qtd_alteracoes = ?, emails_enviados = ?,
                erro = ?
            WHERE id = ?
            """,
            (
                _agora(),
                status,
                qtd_leiautes,
                qtd_arquivos,
                qtd_alteracoes,
                emails_enviados,
                erro,
                execucao_id,
            ),
        )
