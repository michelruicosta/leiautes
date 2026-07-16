# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from persistencia.db import conectar, init_db


def _agora() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _parse(valor: str) -> Any:
    try:
        return json.loads(valor)
    except json.JSONDecodeError:
        return valor


def listar_configuracoes() -> dict[str, Any]:
    init_db()
    with conectar() as conn:
        rows = conn.execute(
            "SELECT chave, valor FROM configuracoes ORDER BY chave"
        ).fetchall()
    return {row["chave"]: _parse(row["valor"]) for row in rows}


def obter_configuracao(chave: str, default: Any = None) -> Any:
    init_db()
    with conectar() as conn:
        row = conn.execute(
            "SELECT valor FROM configuracoes WHERE chave = ?",
            (chave,),
        ).fetchone()
    return _parse(row["valor"]) if row else default


def salvar_configuracao(chave: str, valor: Any) -> None:
    init_db()
    with conectar() as conn:
        conn.execute(
            """
            INSERT INTO configuracoes (chave, valor, atualizado_em)
            VALUES (?, ?, ?)
            ON CONFLICT(chave) DO UPDATE SET
                valor = excluded.valor,
                atualizado_em = excluded.atualizado_em
            """,
            (chave, json.dumps(valor, ensure_ascii=False), _agora()),
        )


def salvar_configuracoes(valores: dict[str, Any]) -> dict[str, Any]:
    for chave, valor in valores.items():
        salvar_configuracao(chave, valor)
    return listar_configuracoes()
