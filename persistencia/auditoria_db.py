# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime
from typing import Optional

from persistencia.db import conectar, init_db


def _agora() -> str:
    return datetime.now().isoformat(timespec="seconds")


def registrar_log(
    *,
    usuario: str = "gestor@finaud.com.br",
    pagina: str,
    acao: str,
    detalhe: str = "",
) -> None:
    init_db()
    with conectar() as conn:
        conn.execute(
            """
            INSERT INTO auditoria (usuario, pagina, acao, detalhe, criado_em)
            VALUES (?, ?, ?, ?, ?)
            """,
            (usuario, pagina, acao, detalhe, _agora()),
        )


def listar_logs(
    *,
    data_de: Optional[str] = None,
    data_ate: Optional[str] = None,
    pagina: Optional[str] = None,
    acao: Optional[str] = None,
    usuario: Optional[str] = None,
    limit: int = 200,
    offset: int = 0,
) -> tuple[list[dict], int]:
    init_db()
    where = []
    params: list[object] = []
    if data_de:
        where.append("date(criado_em) >= date(?)")
        params.append(data_de)
    if data_ate:
        where.append("date(criado_em) <= date(?)")
        params.append(data_ate)
    if pagina:
        if pagina == "Cadastro de Leiautes":
            # Nome atual + nomes antigos na trilha (Leiautes / Páginas Bacen).
            where.append("pagina IN (?, ?, ?)")
            params.extend(["Cadastro de Leiautes", "Páginas Bacen", "Leiautes"])
        else:
            where.append("pagina = ?")
            params.append(pagina)
    if acao:
        where.append("acao = ?")
        params.append(acao)
    if usuario:
        where.append("usuario = ?")
        params.append(usuario)

    sql_where = f"WHERE {' AND '.join(where)}" if where else ""
    limit = max(1, min(limit, 500))
    offset = max(0, offset)
    with conectar() as conn:
        total = conn.execute(
            f"SELECT COUNT(*) AS c FROM auditoria {sql_where}",
            params,
        ).fetchone()["c"]
        rows = conn.execute(
            f"""
            SELECT id, usuario, pagina, acao, detalhe, criado_em
            FROM auditoria
            {sql_where}
            ORDER BY criado_em DESC, id DESC
            LIMIT ? OFFSET ?
            """,
            (*params, limit, offset),
        ).fetchall()
    return [dict(row) for row in rows], int(total)
