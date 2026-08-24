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


def _familia_nome_arquivo(nome_arquivo: str) -> str:
    """Normaliza nome Bacen para achar versão anterior (v7→v8, 202505→202607)."""
    from urllib.parse import unquote

    base = unquote(nome_arquivo or "")
    base = Path(base).name
    # Remove versões tipicas: -v8-vi9, -v7, _v2
    base = re.sub(r"[-_\s]?v\d+-vi\d+", "", base, flags=re.IGNORECASE)
    base = re.sub(r"[-_\s]?v\d+(?=\s|[-_.]|$)", "", base, flags=re.IGNORECASE)
    # Competência YYYYMM (ex.: 2062-202607-Planilha → 2062-Planilha)
    base = re.sub(r"[-_]\d{6}(?=[-_\s.]|$)", "", base)
    base = re.sub(r"\s+", " ", base).strip().lower()
    base = re.sub(r"\s*-\s*", "-", base)
    base = re.sub(r"-{2,}", "-", base)
    return base


def _competencia_yyyymm(nome_arquivo: str) -> Optional[int]:
    """Extrai YYYYMM do nome Bacen (ex.: 2062-202607-v1-...)."""
    from urllib.parse import unquote

    m = re.search(r"(?<!\d)(\d{6})(?!\d)", unquote(nome_arquivo or ""))
    if not m:
        return None
    try:
        val = int(m.group(1))
    except Exception:
        return None
    ano, mes = divmod(val, 100)
    if 1990 <= ano <= 2100 and 1 <= mes <= 12:
        return val
    return None


def _buscar_caminho_versao_parente(
    *,
    nome_arquivo: str,
    leiaute_id: Optional[int],
    excluir_arquivo_id: Optional[int] = None,
    conn: Any = None,
) -> Optional[tuple[str, str, int]]:
    """Retorna (caminho_arquivo, nome_anterior, versao_id) da versão 'irmã' mais próxima."""
    familia = _familia_nome_arquivo(nome_arquivo)
    if not familia or len(familia) < 8:
        return None
    competencia_atual = _competencia_yyyymm(nome_arquivo)

    sql = """
        SELECT ar.id, ar.nome_arquivo, v.caminho_arquivo, ar.atualizado_em, v.id AS versao_id
        FROM arquivos_monitorados ar
        JOIN versoes_arquivos v ON v.id = ar.ultima_versao_id
        WHERE v.caminho_arquivo IS NOT NULL
          AND TRIM(v.caminho_arquivo) != ''
    """
    params: list[Any] = []
    if leiaute_id is not None:
        sql += " AND ar.leiaute_id = ?"
        params.append(leiaute_id)
    if excluir_arquivo_id is not None:
        sql += " AND ar.id != ?"
        params.append(excluir_arquivo_id)
    sql += " ORDER BY ar.atualizado_em DESC, v.id DESC LIMIT 120"

    def _candidatos(rows) -> Optional[tuple[str, str, int]]:
        melhores: list[tuple[tuple, str, str, int]] = []
        for row in rows:
            nome_ant = row["nome_arquivo"] or ""
            if _familia_nome_arquivo(nome_ant) != familia:
                continue
            if nome_ant.strip().lower() == (nome_arquivo or "").strip().lower():
                continue
            caminho = row["caminho_arquivo"]
            path = Path(caminho)
            if not path.is_absolute():
                path = RAIZ / caminho
            if not path.exists():
                continue
            comp_ant = _competencia_yyyymm(nome_ant)
            # Preferir competência imediatamente anterior; senão a mais próxima;
            # por último, a mais recentemente atualizada.
            if competencia_atual is not None and comp_ant is not None:
                if comp_ant < competencia_atual:
                    chave = (0, competencia_atual - comp_ant, -int(row["versao_id"] or 0))
                elif comp_ant > competencia_atual:
                    chave = (2, comp_ant - competencia_atual, -int(row["versao_id"] or 0))
                else:
                    chave = (1, 0, -int(row["versao_id"] or 0))
            else:
                chave = (3, 0, -int(row["versao_id"] or 0))
            melhores.append((chave, str(caminho), nome_ant, int(row["versao_id"])))
        if not melhores:
            return None
        melhores.sort(key=lambda x: x[0])
        _, caminho, nome_ant, versao_id = melhores[0]
        return caminho, nome_ant, versao_id

    if conn is not None:
        rows = conn.execute(sql, params).fetchall()
        return _candidatos(rows)

    init_db()
    with conectar() as c:
        rows = c.execute(sql, params).fetchall()
        return _candidatos(rows)


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
        ("DRSAC", "2030"),
        ("MCC", "MCC"),
    ]
    codigo_sql: Optional[str] = None
    codigo_param: tuple[Any, ...] = ()
    for sigla, numero in pistas:
        if sigla in termo or numero in termo or numero in url:
            if sigla == numero:
                # MCC: codigo no banco é "MCC" (sem sufixo numérico).
                codigo_sql = "SELECT id FROM leiautes_monitorados WHERE codigo = ? LIMIT 1"
                codigo_param = (sigla,)
            else:
                codigo_sql = "SELECT id FROM leiautes_monitorados WHERE codigo LIKE ? LIMIT 1"
                codigo_param = (f"{sigla}-%",)
            break

    if not codigo_sql:
        return None

    with conectar() as conn:
        row = conn.execute(codigo_sql, codigo_param).fetchone()
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
    gerar_evidencia: bool = True,
) -> tuple[int, Optional[int], Optional[int]]:
    """Registra metadados atuais e cria versao/alteracao quando houver mudanca.

    Com `mudou=True` e `gerar_evidencia=False`, grava apenas baseline/versão
    (primeira observação) sem inserir em `alteracoes_detectadas`.

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

            if gerar_evidencia and execucao_id is not None:
                comparacao = None
                nome_anterior_parente = None
                tipo_comparacao = "mesmo_arquivo"
                if not caminho_anterior:
                    tipo_comparacao = "sem_anterior"
                    parente = _buscar_caminho_versao_parente(
                        nome_arquivo=nome_arquivo,
                        leiaute_id=leiaute_id,
                        excluir_arquivo_id=arquivo_id,
                        conn=conn,
                    )
                    if not parente:
                        # Fallback: histórico antigo às vezes ficou sem leiaute_id.
                        parente = _buscar_caminho_versao_parente(
                            nome_arquivo=nome_arquivo,
                            leiaute_id=None,
                            excluir_arquivo_id=arquivo_id,
                            conn=conn,
                        )
                    if parente:
                        caminho_anterior, nome_anterior_parente, versao_parente_id = parente
                        versao_anterior_id = versao_parente_id
                        tipo_comparacao = "versao_pareada"
                if comparar_arquivos and caminho_anterior and caminho_arquivo:
                    try:
                        comparacao = comparar_arquivos(
                            caminho_anterior=caminho_anterior,
                            caminho_atual=caminho_arquivo,
                            tipo_arquivo=tipo,
                        )
                    except Exception as exc:
                        # Não perde o alerta de arquivo novo se o diff PDF/XLSX falhar.
                        comparacao = {
                            "resumo_executivo": (
                                f"Arquivo alterado, mas o diff automático falhou: {exc}"
                            ),
                            "impacto_sugerido": (
                                "Revisar manualmente o arquivo anexo."
                            ),
                            "itens_incluidos": [],
                            "itens_removidos": [],
                            "itens_alterados": [],
                        }
                novo_arquivo = "novo arquivo" in (evidencia or "").lower()
                resumo_cmp = str((comparacao or {}).get("resumo_executivo") or "")
                tem_diff_conteudo = bool(
                    comparacao
                    and (
                        (comparacao.get("itens_incluidos") or [])
                        or (comparacao.get("itens_removidos") or [])
                        or (comparacao.get("itens_alterados") or [])
                    )
                    and "nenhuma diferença" not in resumo_cmp.lower()
                    and "nenhuma diferenca" not in resumo_cmp.lower()
                )

                def _com_rotulo(texto: str) -> str:
                    if tipo_comparacao == "versao_pareada" and nome_anterior_parente:
                        return (
                            f"[Versão pareada · antes: {nome_anterior_parente}] {texto}"
                        )
                    if tipo_comparacao == "sem_anterior":
                        return f"[Sem anterior] {texto}"
                    return f"[Mesmo arquivo] {texto}"

                if tem_diff_conteudo and comparacao:
                    if tipo_comparacao == "versao_pareada" and nome_anterior_parente:
                        resumo = _com_rotulo(
                            f"Arquivo novo na página comparado com {nome_anterior_parente}. "
                            + resumo_cmp
                        )
                    elif novo_arquivo:
                        resumo = _com_rotulo("Arquivo novo na página. " + resumo_cmp)
                    else:
                        resumo = _com_rotulo(resumo_cmp)
                    impacto = comparacao.get("impacto_sugerido") or (
                        "Revisar as diferenças Antes/Depois e o arquivo anexo."
                    )
                    incluidos = list(comparacao.get("itens_incluidos") or [])
                    removidos = list(comparacao.get("itens_removidos") or [])
                    alterados = list(comparacao.get("itens_alterados") or [])
                    if tipo_comparacao == "versao_pareada" and nome_anterior_parente:
                        alterados = [
                            (
                                f'Comparação: mudanca "versão pareada (URLs diferentes)"; '
                                f'antes "{nome_anterior_parente}"; '
                                f'depois "{nome_arquivo}"'
                            )
                        ] + alterados
                elif novo_arquivo:
                    if nome_anterior_parente:
                        resumo = _com_rotulo(
                            f"Arquivo novo na página comparado com {nome_anterior_parente}. "
                            "Diff de conteúdo não apontou diferenças relevantes."
                        )
                        impacto = (
                            "Conferir se a nova versão muda algo além do nome/metadado; "
                            "a estrutura comparada não mostrou alteração material."
                        )
                        incluidos = [
                            f"Novo arquivo na página (pareado com {nome_anterior_parente})."
                        ]
                        removidos = []
                        alterados = [
                            (
                                f'Comparação: mudanca "versão pareada sem diff material"; '
                                f'antes "{nome_anterior_parente}"; '
                                f'depois "{nome_arquivo}"'
                            )
                        ]
                    else:
                        resumo = _com_rotulo(
                            "Arquivo novo na página do Bacen. "
                            "Não há versão anterior da série no histórico para montar Antes/Depois."
                        )
                        impacto = (
                            "Não há com o que comparar automaticamente ainda. "
                            "Na próxima versão da série o robô poderá parear."
                        )
                        incluidos = ["Novo arquivo na página."]
                        removidos = []
                        alterados = []
                elif evidencia:
                    resumo = _com_rotulo(f"Alteracao detectada por metadados: {evidencia}")
                    impacto = "Revisar o arquivo alterado e avaliar impacto operacional."
                    incluidos = []
                    removidos = []
                    alterados = [evidencia]
                else:
                    resumo = _com_rotulo("Alteracao detectada por metadados do arquivo.")
                    impacto = "Revisar o arquivo alterado e avaliar impacto operacional."
                    incluidos = []
                    removidos = []
                    alterados = []
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
