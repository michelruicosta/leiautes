# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Optional

from persistencia.db import conectar, init_db


def obter_ultima_execucao() -> Optional[dict]:
    init_db()
    with conectar() as conn:
        row = conn.execute(
            """
            SELECT * FROM execucoes
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()
    return dict(row) if row else None


def obter_execucao(execucao_id: int) -> Optional[dict]:
    init_db()
    with conectar() as conn:
        row = conn.execute(
            """
            SELECT * FROM execucoes
            WHERE id = ?
            """,
            (execucao_id,),
        ).fetchone()
    return dict(row) if row else None


def listar_execucoes(*, limit: int = 50, offset: int = 0) -> tuple[list[dict], int]:
    init_db()
    limit = max(1, min(limit, 200))
    offset = max(0, offset)
    with conectar() as conn:
        total = conn.execute("SELECT COUNT(*) AS c FROM execucoes").fetchone()["c"]
        rows = conn.execute(
            """
            SELECT * FROM execucoes
            ORDER BY id DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()
    return [dict(row) for row in rows], int(total)


def resumo_dashboard() -> dict:
    init_db()
    with conectar() as conn:
        ultima = conn.execute(
            "SELECT * FROM execucoes ORDER BY id DESC LIMIT 1"
        ).fetchone()
        qtd_leiautes = conn.execute(
            "SELECT COUNT(*) AS c FROM leiautes_monitorados WHERE ativo = 1"
        ).fetchone()["c"]
        qtd_arquivos = conn.execute(
            "SELECT COUNT(*) AS c FROM arquivos_monitorados"
        ).fetchone()["c"]
        qtd_alteracoes = conn.execute(
            "SELECT COUNT(*) AS c FROM alteracoes_detectadas"
        ).fetchone()["c"]
        recentes = conn.execute(
            """
            SELECT
                a.id,
                a.execucao_id,
                COALESCE(l.codigo, '') AS leiaute_codigo,
                ar.nome_arquivo AS arquivo_nome,
                ar.tipo_arquivo AS arquivo_tipo,
                a.resumo_executivo,
                a.impacto_sugerido,
                a.status,
                a.criado_em,
                a.itens_incluidos,
                a.itens_removidos,
                a.itens_alterados
            FROM alteracoes_detectadas a
            JOIN arquivos_monitorados ar ON ar.id = a.arquivo_id
            LEFT JOIN leiautes_monitorados l ON l.id = ar.leiaute_id
            ORDER BY a.id DESC
            LIMIT 5
            """
        ).fetchall()
    return {
        "ultima_execucao": dict(ultima) if ultima else None,
        "qtd_leiautes": int(qtd_leiautes),
        "qtd_arquivos": int(qtd_arquivos),
        "qtd_alteracoes": int(qtd_alteracoes),
        "alteracoes_recentes": [dict(row) for row in recentes],
    }


def contar_resultados_execucao(execucao_id: int) -> dict[str, int]:
    init_db()
    with conectar() as conn:
        qtd_arquivos = conn.execute(
            "SELECT COUNT(*) AS c FROM versoes_arquivos WHERE execucao_id = ?",
            (execucao_id,),
        ).fetchone()["c"]
        qtd_alteracoes = conn.execute(
            "SELECT COUNT(*) AS c FROM alteracoes_detectadas WHERE execucao_id = ?",
            (execucao_id,),
        ).fetchone()["c"]
        qtd_leiautes = conn.execute(
            """
            SELECT COUNT(DISTINCT ar.leiaute_id) AS c
            FROM versoes_arquivos v
            JOIN arquivos_monitorados ar ON ar.id = v.arquivo_id
            WHERE v.execucao_id = ? AND ar.leiaute_id IS NOT NULL
            """,
            (execucao_id,),
        ).fetchone()["c"]
    return {
        "qtd_leiautes": int(qtd_leiautes),
        "qtd_arquivos": int(qtd_arquivos),
        "qtd_alteracoes": int(qtd_alteracoes),
    }
