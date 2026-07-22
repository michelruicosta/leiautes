# -*- coding: utf-8 -*-
"""Valida se o banco possui evidências úteis por tipo de arquivo."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DB = BASE / "dados" / "leiautes.db"
TIPOS_ESPERADOS = {"pdf", "txt", "xls", "xlsx", "xml", "xsd", "zip"}


def _lista(valor: str | None) -> list[str]:
    if not valor:
        return []
    parsed = json.loads(valor)
    return parsed if isinstance(parsed, list) else []


def _tem_localizacao(tipo: str, texto: str) -> bool:
    texto_lower = texto.lower()
    if tipo == "pdf":
        return "página" in texto_lower and "linha" in texto_lower
    if tipo in {"txt", "xml"}:
        return "linha" in texto_lower
    if tipo in {"xls", "xlsx"}:
        return "aba" in texto_lower and "célula" in texto_lower
    if tipo == "xsd":
        return "linha" in texto_lower and ("schema" in texto_lower or "campo" in texto_lower)
    if tipo == "zip":
        return "arquivo interno" in texto_lower
    return bool(texto.strip())


def _tem_antes_depois(texto: str) -> bool:
    texto_lower = texto.lower()
    return "antes" in texto_lower and "depois" in texto_lower


def main() -> None:
    if not DB.exists():
        raise SystemExit(f"Banco não encontrado: {DB}")

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT
            ar.tipo_arquivo,
            ar.nome_arquivo,
            a.itens_incluidos,
            a.itens_removidos,
            a.itens_alterados
        FROM alteracoes_detectadas a
        JOIN arquivos_monitorados ar ON ar.id = a.arquivo_id
        ORDER BY a.id DESC
        """
    ).fetchall()

    encontrados: dict[str, sqlite3.Row] = {}
    for row in rows:
        tipo = str(row["tipo_arquivo"]).lower()
        if tipo in encontrados or tipo not in TIPOS_ESPERADOS:
            continue
        itens = [
            *_lista(row["itens_incluidos"]),
            *_lista(row["itens_removidos"]),
            *_lista(row["itens_alterados"]),
        ]
        if any(_tem_localizacao(tipo, item) for item in itens):
            encontrados[tipo] = row

    faltantes = sorted(TIPOS_ESPERADOS - set(encontrados))
    if faltantes:
        raise SystemExit(f"Sem evidência detalhada para: {', '.join(faltantes)}")

    sem_antes_depois = []
    for tipo, row in encontrados.items():
        alterados = _lista(row["itens_alterados"])
        if alterados and not any(_tem_antes_depois(item) for item in alterados):
            sem_antes_depois.append(tipo)

    if sem_antes_depois:
        raise SystemExit(
            "Alterações sem antes/depois para: " + ", ".join(sorted(sem_antes_depois))
        )

    for tipo in sorted(encontrados):
        row = encontrados[tipo]
        print(f"OK {tipo}: {row['nome_arquivo']}")


if __name__ == "__main__":
    main()
