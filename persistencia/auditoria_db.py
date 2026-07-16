# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime

from persistencia.db import conectar, init_db


def registrar_auditoria(
    *,
    usuario: str = "sistema",
    pagina: str,
    acao: str,
    detalhe: str = "",
) -> int:
    init_db()
    with conectar() as conn:
        cur = conn.execute(
            """
            INSERT INTO auditoria (usuario, pagina, acao, detalhe, criado_em)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                usuario,
                pagina,
                acao,
                detalhe,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        return int(cur.lastrowid)
