# -*- coding: utf-8 -*-
"""Listagem e download das versões de arquivos guardadas em storage."""
from __future__ import annotations

import urllib.error
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from persistencia.arquivos_db import _competencia_yyyymm
from persistencia.db import conectar, init_db

RAIZ = Path(__file__).resolve().parent.parent

# Cache do HEAD no Bacen — evita bater no site a cada abertura da tela.
_TTL_VERIFICACAO_URL = timedelta(hours=12)


def _agora() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _resolver_caminho(caminho: str | None) -> Path | None:
    if not caminho or not str(caminho).strip():
        return None
    path = Path(caminho)
    if not path.is_absolute():
        path = RAIZ / path
    return path if path.exists() and path.is_file() else None


def _ensure_colunas_url(conn: Any) -> None:
    cols = {row[1] for row in conn.execute("PRAGMA table_info(arquivos_monitorados)")}
    if "url_http_status" not in cols:
        conn.execute(
            "ALTER TABLE arquivos_monitorados ADD COLUMN url_http_status INTEGER"
        )
    if "url_verificado_em" not in cols:
        conn.execute(
            "ALTER TABLE arquivos_monitorados ADD COLUMN url_verificado_em TEXT"
        )


def _cache_url_fresco(verificado_em: str | None) -> bool:
    if not verificado_em:
        return False
    try:
        quando = datetime.fromisoformat(verificado_em)
    except ValueError:
        return False
    return datetime.now() - quando < _TTL_VERIFICACAO_URL


def _head_url_bacen(url: str, timeout: float = 12.0) -> int:
    """Retorna código HTTP do HEAD (ou 0 se falhar sem código)."""
    try:
        req = urllib.request.Request(
            url,
            method="HEAD",
            headers={"User-Agent": "leiautes_bacen/1.0 (+monitoramento)"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return int(resp.status)
    except urllib.error.HTTPError as exc:
        return int(exc.code or 0)
    except Exception:
        return 0


def _url_fora_do_site(
    conn: Any,
    *,
    arquivo_id: int,
    url: str | None,
    status_cache: int | None,
    verificado_em: str | None,
) -> bool:
    """True se a URL do Bacen não responde OK — cópia local pode existir mesmo assim."""
    if not url or not str(url).strip():
        return True
    if _cache_url_fresco(verificado_em) and status_cache is not None:
        return int(status_cache) != 200

    status = _head_url_bacen(str(url).strip())
    agora = _agora()
    conn.execute(
        """
        UPDATE arquivos_monitorados
        SET url_http_status = ?, url_verificado_em = ?
        WHERE id = ?
        """,
        (status, agora, arquivo_id),
    )
    return status != 200


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
        _ensure_colunas_url(conn)
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
                ar.id AS arquivo_id,
                ar.nome_arquivo AS arquivo_nome,
                ar.tipo_arquivo AS arquivo_tipo,
                ar.url AS url_bacen,
                ar.url_http_status,
                ar.url_verificado_em,
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

        # Uma verificação por arquivo_id (várias versões do mesmo arquivo compartilham URL).
        cache_fora: dict[int, bool] = {}
        itens: list[dict[str, Any]] = []
        for row in rows:
            path = _resolver_caminho(row["caminho_arquivo"])
            if path is None:
                continue
            nome = row["arquivo_nome"] or ""
            comp = _competencia_yyyymm(nome)
            vigencia = str(comp) if comp is not None else ""
            arquivo_id = int(row["arquivo_id"])
            if arquivo_id not in cache_fora:
                cache_fora[arquivo_id] = _url_fora_do_site(
                    conn,
                    arquivo_id=arquivo_id,
                    url=row["url_bacen"],
                    status_cache=row["url_http_status"],
                    verificado_em=row["url_verificado_em"],
                )
            itens.append(
                {
                    "id": row["id"],
                    "capturado_em": row["capturado_em"],
                    "leiaute_codigo": row["leiaute_codigo"] or "",
                    "arquivo_nome": nome,
                    "arquivo_tipo": row["arquivo_tipo"] or "",
                    "vigencia": vigencia,
                    "fora_do_site": cache_fora[arquivo_id],
                }
            )
        conn.commit()
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
