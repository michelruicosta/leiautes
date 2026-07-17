# -*- coding: utf-8 -*-
"""Recalcula resumo/itens das alterações usando o comparador atual."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from backend.app.services.comparador_arquivos import comparar_arquivos
from persistencia.db import conectar


def recalcular(tipo: str | None = None) -> int:
    where = "WHERE ar.tipo_arquivo = ?" if tipo else ""
    params = (tipo,) if tipo else ()
    atualizados = 0
    with conectar() as conn:
        rows = conn.execute(
            f"""
            SELECT
                a.id,
                ar.tipo_arquivo,
                va.caminho_arquivo AS caminho_atual,
                vp.caminho_arquivo AS caminho_anterior
            FROM alteracoes_detectadas a
            JOIN arquivos_monitorados ar ON ar.id = a.arquivo_id
            JOIN versoes_arquivos va ON va.id = a.versao_atual_id
            LEFT JOIN versoes_arquivos vp ON vp.id = a.versao_anterior_id
            {where}
            ORDER BY a.id
            """,
            params,
        ).fetchall()

        for row in rows:
            comparacao = comparar_arquivos(
                caminho_anterior=row["caminho_anterior"],
                caminho_atual=row["caminho_atual"],
                tipo_arquivo=row["tipo_arquivo"],
            )
            if not comparacao:
                continue
            conn.execute(
                """
                UPDATE alteracoes_detectadas
                SET resumo_executivo = ?,
                    impacto_sugerido = ?,
                    itens_incluidos = ?,
                    itens_removidos = ?,
                    itens_alterados = ?
                WHERE id = ?
                """,
                (
                    comparacao.get("resumo_executivo", ""),
                    comparacao.get("impacto_sugerido", ""),
                    json.dumps(comparacao.get("itens_incluidos", []), ensure_ascii=False),
                    json.dumps(comparacao.get("itens_removidos", []), ensure_ascii=False),
                    json.dumps(comparacao.get("itens_alterados", []), ensure_ascii=False),
                    row["id"],
                ),
            )
            atualizados += 1
    return atualizados


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tipo", default=None)
    args = parser.parse_args()
    total = recalcular(args.tipo)
    print(f"Alterações recalculadas: {total}")


if __name__ == "__main__":
    main()
