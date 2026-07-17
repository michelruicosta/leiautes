# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import Optional

from persistencia.db import conectar, init_db


def _agora() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _parse_lista(valor: Optional[str]) -> list[str]:
    if not valor:
        return []
    try:
        parsed = json.loads(valor)
        return parsed if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        return []


def _row_leiaute(row) -> dict:
    data = dict(row)
    data["tipos_arquivo"] = _parse_lista(data.get("tipos_arquivo"))
    data["ativo"] = bool(data.get("ativo"))
    return data


def listar_leiautes(*, ativos: Optional[bool] = None) -> tuple[list[dict], int]:
    init_db()
    where = ""
    params: list[object] = []
    if ativos is not None:
        where = "WHERE ativo = ?"
        params.append(1 if ativos else 0)
    with conectar() as conn:
        total = conn.execute(
            f"SELECT COUNT(*) AS c FROM leiautes_monitorados {where}",
            params,
        ).fetchone()["c"]
        rows = conn.execute(
            f"""
            SELECT * FROM leiautes_monitorados
            {where}
            ORDER BY categoria, codigo
            """,
            params,
        ).fetchall()
    return [_row_leiaute(row) for row in rows], int(total)


def obter_leiaute(leiaute_id: int) -> Optional[dict]:
    init_db()
    with conectar() as conn:
        row = conn.execute(
            "SELECT * FROM leiautes_monitorados WHERE id = ?",
            (leiaute_id,),
        ).fetchone()
    return _row_leiaute(row) if row else None


def criar_leiaute(data: dict) -> int:
    init_db()
    agora = _agora()
    with conectar() as conn:
        cur = conn.execute(
            """
            INSERT INTO leiautes_monitorados (
                codigo, nome, categoria, url_bacen, tipos_arquivo,
                ativo, criado_em, atualizado_em
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["codigo"],
                data["nome"],
                data["categoria"],
                data["url_bacen"],
                json.dumps(data.get("tipos_arquivo", []), ensure_ascii=False),
                1 if data.get("ativo", True) else 0,
                agora,
                agora,
            ),
        )
        return int(cur.lastrowid)


def atualizar_leiaute(leiaute_id: int, data: dict) -> Optional[dict]:
    atual = obter_leiaute(leiaute_id)
    if not atual:
        return None

    novo = {**atual, **{k: v for k, v in data.items() if v is not None}}
    with conectar() as conn:
        conn.execute(
            """
            UPDATE leiautes_monitorados
            SET codigo = ?, nome = ?, categoria = ?, url_bacen = ?,
                tipos_arquivo = ?, ativo = ?, atualizado_em = ?
            WHERE id = ?
            """,
            (
                novo["codigo"],
                novo["nome"],
                novo["categoria"],
                novo["url_bacen"],
                json.dumps(novo.get("tipos_arquivo", []), ensure_ascii=False),
                1 if novo.get("ativo", True) else 0,
                _agora(),
                leiaute_id,
            ),
        )
    return obter_leiaute(leiaute_id)


def excluir_leiaute(leiaute_id: int) -> bool:
    init_db()
    try:
        with conectar() as conn:
            cur = conn.execute(
                "DELETE FROM leiautes_monitorados WHERE id = ?",
                (leiaute_id,),
            )
            return cur.rowcount > 0
    except sqlite3.IntegrityError:
        return False
