# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from persistencia.db import conectar, init_db

try:
    from backend.app.services.comparador_arquivos import comparar_arquivos
except Exception:
    comparar_arquivos = None

RAIZ = Path(__file__).resolve().parent.parent


def _agora() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _tipo_arquivo(nome_arquivo: str) -> str:
    ext = Path(nome_arquivo).suffix.lower().lstrip(".")
    return ext or "desconhecido"


def _slug(texto: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", texto.strip())
    return slug.strip("._") or "arquivo"


def salvar_conteudo_versao(
    *,
    conteudo: bytes,
    nome_arquivo: str,
    categoria: Optional[str] = None,
    storage_dir: Optional[str] = None,
) -> str:
    agora = datetime.now()
    tipo = _tipo_arquivo(nome_arquivo)
    categoria_slug = _slug(categoria or "sem_categoria")
    nome_slug = _slug(nome_arquivo)
    base = Path(storage_dir) if storage_dir else RAIZ / "storage" / "arquivos"
    destino_dir = base / agora.strftime("%Y") / agora.strftime("%m") / agora.strftime("%d") / categoria_slug / tipo
    destino_dir.mkdir(parents=True, exist_ok=True)

    destino = destino_dir / f"{agora.strftime('%H%M%S_%f')}_{nome_slug}"
    destino.write_bytes(conteudo)
    return str(destino.relative_to(RAIZ) if destino.is_relative_to(RAIZ) else destino)


def _buscar_leiaute_id(categoria: Optional[str], url: str) -> Optional[int]:
    init_db()
    termo = (categoria or "").upper()
    pistas = [
        ("SCD", "4111"),
        ("DDR", "2011"),
        ("DRM", "2060"),
        ("DLO", "2061"),
        ("DLI", "2062"),
        ("DRL", "2160"),
    ]
    codigo_like: Optional[str] = None
    for sigla, numero in pistas:
        if sigla in termo or numero in termo or numero in url:
            codigo_like = f"{sigla}-%"
            break

    if not codigo_like:
        return None

    with conectar() as conn:
        row = conn.execute(
            "SELECT id FROM leiautes_monitorados WHERE codigo LIKE ? LIMIT 1",
            (codigo_like,),
        ).fetchone()
    return int(row["id"]) if row else None


def registrar_arquivo_observado(
    *,
    url: str,
    nome_arquivo: str,
    info: dict[str, Any],
    categoria: Optional[str] = None,
    execucao_id: Optional[int] = None,
    mudou: bool = False,
    evidencia: str = "",
    caminho_arquivo: Optional[str] = None,
) -> tuple[int, Optional[int], Optional[int]]:
    """Registra metadados atuais e cria versao/alteracao quando houver mudanca.

    Retorna `(arquivo_id, versao_id, alteracao_id)`.
    """
    init_db()
    agora = _agora()
    tipo = _tipo_arquivo(nome_arquivo)
    leiaute_id = _buscar_leiaute_id(categoria, url)
    hash_conteudo = info.get("partial_fp")

    with conectar() as conn:
        existente = conn.execute(
            "SELECT id, ultima_versao_id FROM arquivos_monitorados WHERE url = ?",
            (url,),
        ).fetchone()

        if existente:
            arquivo_id = int(existente["id"])
            versao_anterior_id = (
                int(existente["ultima_versao_id"])
                if existente["ultima_versao_id"] is not None
                else None
            )
            conn.execute(
                """
                UPDATE arquivos_monitorados
                SET leiaute_id = COALESCE(?, leiaute_id),
                    nome_arquivo = ?,
                    tipo_arquivo = ?,
                    etag = ?,
                    last_modified = ?,
                    content_length = ?,
                    final_url = ?,
                    partial_fp = ?,
                    hash_conteudo = ?,
                    ultima_verificacao_em = ?,
                    atualizado_em = ?
                WHERE id = ?
                """,
                (
                    leiaute_id,
                    nome_arquivo,
                    tipo,
                    info.get("etag"),
                    info.get("last_modified"),
                    info.get("content_length"),
                    info.get("final_url"),
                    info.get("partial_fp"),
                    hash_conteudo,
                    info.get("checked_at") or agora,
                    agora,
                    arquivo_id,
                ),
            )
        else:
            cur = conn.execute(
                """
                INSERT INTO arquivos_monitorados (
                    leiaute_id, url, nome_arquivo, tipo_arquivo, etag,
                    last_modified, content_length, final_url, partial_fp,
                    hash_conteudo, ultima_verificacao_em, criado_em, atualizado_em
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    leiaute_id,
                    url,
                    nome_arquivo,
                    tipo,
                    info.get("etag"),
                    info.get("last_modified"),
                    info.get("content_length"),
                    info.get("final_url"),
                    info.get("partial_fp"),
                    hash_conteudo,
                    info.get("checked_at") or agora,
                    agora,
                    agora,
                ),
            )
            arquivo_id = int(cur.lastrowid)
            versao_anterior_id = None

        versao_id: Optional[int] = None
        alteracao_id: Optional[int] = None
        if mudou:
            caminho_anterior = None
            if versao_anterior_id is not None:
                row_ant = conn.execute(
                    """
                    SELECT caminho_arquivo
                    FROM versoes_arquivos
                    WHERE id = ?
                    """,
                    (versao_anterior_id,),
                ).fetchone()
                caminho_anterior = row_ant["caminho_arquivo"] if row_ant else None

            cur = conn.execute(
                """
                INSERT INTO versoes_arquivos (
                    arquivo_id, execucao_id, caminho_arquivo, caminho_texto,
                    hash_conteudo, tamanho_bytes, metadados, criado_em
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    arquivo_id,
                    execucao_id,
                    caminho_arquivo,
                    None,
                    hash_conteudo,
                    int(info["content_length"]) if str(info.get("content_length") or "").isdigit() else None,
                    json.dumps(info, ensure_ascii=False),
                    agora,
                ),
            )
            versao_id = int(cur.lastrowid)
            conn.execute(
                """
                UPDATE arquivos_monitorados
                SET ultima_versao_id = ?, atualizado_em = ?
                WHERE id = ?
                """,
                (versao_id, agora, arquivo_id),
            )

            if execucao_id is not None:
                comparacao = None
                if comparar_arquivos and caminho_anterior and caminho_arquivo:
                    comparacao = comparar_arquivos(
                        caminho_anterior=caminho_anterior,
                        caminho_atual=caminho_arquivo,
                        tipo_arquivo=tipo,
                    )
                resumo = (
                    comparacao.get("resumo_executivo")
                    if comparacao
                    else (
                        f"Alteracao detectada por metadados: {evidencia}"
                        if evidencia
                        else "Alteracao detectada por metadados do arquivo."
                    )
                )
                impacto = (
                    comparacao.get("impacto_sugerido")
                    if comparacao
                    else "Revisar o arquivo alterado e avaliar impacto operacional."
                )
                incluidos = (
                    comparacao.get("itens_incluidos", []) if comparacao else []
                )
                removidos = (
                    comparacao.get("itens_removidos", []) if comparacao else []
                )
                alterados = (
                    comparacao.get("itens_alterados", [])
                    if comparacao
                    else ([evidencia] if evidencia else [])
                )
                cur_alt = conn.execute(
                    """
                    INSERT INTO alteracoes_detectadas (
                        execucao_id, arquivo_id, versao_anterior_id, versao_atual_id,
                        resumo_executivo, impacto_sugerido, itens_incluidos,
                        itens_removidos, itens_alterados, status, criado_em
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pendente', ?)
                    """,
                    (
                        execucao_id,
                        arquivo_id,
                        versao_anterior_id,
                        versao_id,
                        resumo,
                        impacto,
                        json.dumps(incluidos, ensure_ascii=False),
                        json.dumps(removidos, ensure_ascii=False),
                        json.dumps(alterados, ensure_ascii=False),
                        agora,
                    ),
                )
                alteracao_id = int(cur_alt.lastrowid)

    return arquivo_id, versao_id, alteracao_id
