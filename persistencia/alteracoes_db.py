# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from typing import Optional

from persistencia.db import conectar, init_db


def _parse_lista(valor: str | None) -> list[str]:
    if not valor:
        return []
    try:
        parsed = json.loads(valor)
        return parsed if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        return []


def _row_alteracao(row) -> dict:
    data = dict(row)
    data["itens_incluidos"] = _parse_lista(data.get("itens_incluidos"))
    data["itens_removidos"] = _parse_lista(data.get("itens_removidos"))
    data["itens_alterados"] = _parse_lista(data.get("itens_alterados"))
    return data


def listar_alteracoes(
    *,
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    leiaute_codigo: Optional[str] = None,
) -> tuple[list[dict], int]:
    init_db()
    limit = max(1, min(limit, 200))
    offset = max(0, offset)
    where: list[str] = []
    params: list[object] = []

    if status:
        where.append("a.status = ?")
        params.append(status)
    if leiaute_codigo:
        where.append("l.codigo = ?")
        params.append(leiaute_codigo)

    sql_where = f"WHERE {' AND '.join(where)}" if where else ""
    with conectar() as conn:
        total = conn.execute(
            f"""
            SELECT COUNT(*) AS c
            FROM alteracoes_detectadas a
            JOIN arquivos_monitorados ar ON ar.id = a.arquivo_id
            LEFT JOIN leiautes_monitorados l ON l.id = ar.leiaute_id
            {sql_where}
            """,
            params,
        ).fetchone()["c"]
        rows = conn.execute(
            f"""
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
            {sql_where}
            ORDER BY a.id DESC
            LIMIT ? OFFSET ?
            """,
            [*params, limit, offset],
        ).fetchall()
    return [_row_alteracao(row) for row in rows], int(total)


def obter_alteracao(alteracao_id: int) -> Optional[dict]:
    init_db()
    with conectar() as conn:
        row = conn.execute(
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
            WHERE a.id = ?
            """,
            (alteracao_id,),
        ).fetchone()
    return _row_alteracao(row) if row else None
