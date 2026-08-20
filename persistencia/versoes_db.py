# -*- coding: utf-8 -*-
"""Listagem e download das versões de arquivos guardadas em storage."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from persistencia.arquivos_db import _competencia_yyyymm, _familia_nome_arquivo
from persistencia.db import conectar, init_db

RAIZ = Path(__file__).resolve().parent.parent


def _resolver_caminho(caminho: str | None) -> Path | None:
    if not caminho or not str(caminho).strip():
        return None
    path = Path(caminho)
    if not path.is_absolute():
        path = RAIZ / path
    return path if path.exists() and path.is_file() else None


def listar_versoes(
    *,
    limit: int = 100,
    offset: int = 0,
    leiaute_codigo: Optional[str] = None,
    tipo: Optional[str] = None,
    busca: Optional[str] = None,
) -> tuple[list[dict[str, Any]], int]:
    init_db()
    limit = max(1, min(limit, 500))
    offset = max(0, offset)
    where: list[str] = [
        "v.caminho_arquivo IS NOT NULL",
        "TRIM(v.caminho_arquivo) != ''",
    ]
    params: list[object] = []

    if leiaute_codigo:
        where.append("COALESCE(l.codigo, '') = ?")
        params.append(leiaute_codigo)
    if tipo:
        where.append("LOWER(ar.tipo_arquivo) = ?")
        params.append(tipo.lower())
    if busca:
        where.append(
            "(LOWER(ar.nome_arquivo) LIKE ? OR LOWER(COALESCE(l.codigo, '')) LIKE ?)"
        )
        like = f"%{busca.lower()}%"
        params.extend([like, like])

    sql_where = f"WHERE {' AND '.join(where)}"
    with conectar() as conn:
        total = conn.execute(
            f"""
            SELECT COUNT(*) AS c
            FROM versoes_arquivos v
            JOIN arquivos_monitorados ar ON ar.id = v.arquivo_id
            LEFT JOIN leiautes_monitorados l ON l.id = ar.leiaute_id
            {sql_where}
            """,
            params,
        ).fetchone()["c"]

        rows = conn.execute(
            f"""
            SELECT
                v.id,
                v.criado_em AS capturado_em,
                v.caminho_arquivo,
                ar.nome_arquivo AS arquivo_nome,
                ar.tipo_arquivo AS arquivo_tipo,
                ar.url AS url_bacen,
                COALESCE(l.codigo, '') AS leiaute_codigo
            FROM versoes_arquivos v
            JOIN arquivos_monitorados ar ON ar.id = v.arquivo_id
            LEFT JOIN leiautes_monitorados l ON l.id = ar.leiaute_id
            {sql_where}
            ORDER BY v.criado_em DESC, v.id DESC
            LIMIT ? OFFSET ?
            """,
            [*params, limit, offset],
        ).fetchall()

        # Máxima vigência por família em todo o acervo (não só na página).
        max_por_familia: dict[str, int] = {}
        for row in conn.execute(
            """
            SELECT ar.nome_arquivo
            FROM versoes_arquivos v
            JOIN arquivos_monitorados ar ON ar.id = v.arquivo_id
            WHERE v.caminho_arquivo IS NOT NULL AND TRIM(v.caminho_arquivo) != ''
            """
        ).fetchall():
            nome = row["nome_arquivo"] or ""
            familia = _familia_nome_arquivo(nome)
            comp = _competencia_yyyymm(nome)
            if not familia or comp is None:
                continue
            atual = max_por_familia.get(familia)
            if atual is None or comp > atual:
                max_por_familia[familia] = comp

        itens: list[dict[str, Any]] = []
        for row in rows:
            nome = row["arquivo_nome"] or ""
            familia = _familia_nome_arquivo(nome)
            comp = _competencia_yyyymm(nome)
            vigencia = str(comp) if comp is not None else ""
            max_fam = max_por_familia.get(familia) if familia else None
            fora = bool(
                comp is not None and max_fam is not None and comp < max_fam
            )
            path = _resolver_caminho(row["caminho_arquivo"])
            if path is None:
                continue
            itens.append(
                {
                    "id": row["id"],
                    "capturado_em": row["capturado_em"],
                    "leiaute_codigo": row["leiaute_codigo"] or "",
                    "arquivo_nome": nome,
                    "arquivo_tipo": row["arquivo_tipo"] or "",
                    "vigencia": vigencia,
                    "fora_do_site": fora,
                }
            )

        return itens, int(total)


def obter_caminho_download(versao_id: int) -> tuple[Path, str] | None:
    init_db()
    with conectar() as conn:
        row = conn.execute(
            """
            SELECT v.caminho_arquivo, ar.nome_arquivo
            FROM versoes_arquivos v
            JOIN arquivos_monitorados ar ON ar.id = v.arquivo_id
            WHERE v.id = ?
            """,
            (versao_id,),
        ).fetchone()
    if not row:
        return None
    path = _resolver_caminho(row["caminho_arquivo"])
    if path is None:
        return None
    nome = row["nome_arquivo"] or path.name
    return path, nome
