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


_MESES_NO_NOME = (
    r"janeiro|fevereiro|mar[cç]o|abril|maio|junho|julho|agosto|setembro|"
    r"outubro|novembro|dezembro|jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez"
)


def _sem_acento(texto: str) -> str:
    import unicodedata

    nfd = unicodedata.normalize("NFD", texto or "")
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


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
    # Mês no sufixo (v10_Abril2021, V5_Jul26) — mesmo papel das instruções/críticas
    base = re.sub(
        rf"[-_\s]?(?:{_MESES_NO_NOME})\s*\d{{2,4}}(?=\s|[-_.]|$)",
        "",
        base,
        flags=re.IGNORECASE,
    )
    base = _sem_acento(base).lower().replace("_", "-")
    base = re.sub(r"\s+", " ", base).strip()
    base = re.sub(r"\s*-\s*", "-", base)
    base = re.sub(r"-{2,}", "-", base)
    return base


# Papéis cravados (Michel 26/08/2026): nome diferente, mesmo documento.
_PAPEIS_EQUIVALENTES: tuple[tuple[str, ...], ...] = (
    (
        "dlo-criticas",
        "Críticas de Pós-Processamento DLO_2061_V5 Ajustada.xlsx",
        "2061-202411-v3-Críticas de pós processamento.xlsx",
    ),
    (
        "ddr-instrucoes",
        "2011-202407-v7-vi7-Instruções de Preenchimento.pdf",
        "Instruções de Preenchimento  2011 - versão publicação V3.01032021.pdf",
    ),
    (
        "ddr-leiaute-xls",
        "Leiaute DDR - 2011 Versão Publicação.xls",
        "Leiaute_DDR_2011_Versao_Publicacao.v5 01072023.xls",
    ),
    (
        "scd-instrucoes",
        "Documento de Saldos Contábeis Diários - Instruções de Preenchimento.pdf",
        "saldosDiariosInstrucoesPreenchimentoV2.pdf",
    ),
)


def _chave_papel(nome_arquivo: str) -> str:
    """Identifica o papel (função no site), inclusive quando o nome mudou."""
    fam = _familia_nome_arquivo(nome_arquivo)
    for canon, *exemplos in _PAPEIS_EQUIVALENTES:
        if fam in {_familia_nome_arquivo(ex) for ex in exemplos}:
            return canon
    return fam


def _extensao_arquivo(nome_arquivo: str) -> str:
    from urllib.parse import unquote

    return Path(unquote(nome_arquivo or "")).suffix.lower()


def _versao_no_nome(nome_arquivo: str) -> Optional[int]:
    """Extrai v2, v5, _v3 do nome (ex.: 2062_v3.xsd, Esquema de validação XSD v5.xsd)."""
    from urllib.parse import unquote

    base = Path(unquote(nome_arquivo or "")).name
    m = re.search(r"(?:^|[^A-Za-z0-9])v(\d+)(?=[^0-9]|$)", base, flags=re.IGNORECASE)
    if not m:
        return None
    try:
        return int(m.group(1))
    except Exception:
        return None


def _versao_interna_no_nome(nome_arquivo: str) -> Optional[int]:
    """Extrai -vi2, -vi16 (versão interna Bacen no mesmo mês)."""
    from urllib.parse import unquote

    base = Path(unquote(nome_arquivo or "")).name
    m = re.search(r"-vi(\d+)(?=[^0-9]|$)", base, flags=re.IGNORECASE)
    if not m:
        return None
    try:
        return int(m.group(1))
    except Exception:
        return None


def _resolver_caminho_armazenado(caminho: str) -> Optional[Path]:
    path = Path(caminho)
    if not path.is_absolute():
        path = RAIZ / caminho
    return path if path.exists() else None


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


FORMATOS_NOME_NOVO_UNICO = {".xsd"}


def _chave_candidato(nome_arquivo: str, nome_ant: str, *, por_familia: bool) -> tuple:
    """Menor chave = melhor par. Mesmo papel usa competência; nome novo usa número de versão."""
    v_ant = _versao_no_nome(nome_ant) or 0
    vi_ant = _versao_interna_no_nome(nome_ant) or 0
    desempate = (-v_ant, -vi_ant, nome_ant.lower())
    if por_familia:
        competencia_atual = _competencia_yyyymm(nome_arquivo)
        comp_ant = _competencia_yyyymm(nome_ant)
        if competencia_atual is not None and comp_ant is not None:
            if comp_ant < competencia_atual:
                return (0, competencia_atual - comp_ant) + desempate
            if comp_ant > competencia_atual:
                return (2, comp_ant - competencia_atual) + desempate
            return (1, 0) + desempate
        v_atual = _versao_no_nome(nome_arquivo)
        if v_atual is not None and v_ant:
            if v_ant < v_atual:
                return (3, v_atual - v_ant) + desempate
            return (5, v_ant) + desempate
        return (4, 0) + desempate
    v_atual = _versao_no_nome(nome_arquivo)
    if v_atual is not None and v_ant:
        if v_ant < v_atual:
            return (0, v_atual - v_ant) + desempate
        return (2, v_ant) + desempate
    return (1, 0) + desempate


def _melhor_nome(nome_arquivo: str, candidatos: list[str], *, por_familia: bool) -> Optional[str]:
    if not candidatos:
        return None
    ordenados = sorted(
        candidatos,
        key=lambda n: _chave_candidato(nome_arquivo, n, por_familia=por_familia),
    )
    return ordenados[0]


def escolher_nome_versao_parente(
    nome_arquivo: str,
    candidatos: list[str],
    *,
    permitir_unico_formato: bool = True,
) -> Optional[str]:
    """Com qual arquivo comparar. None = não comparar (não inventa o par).

    1) Mesmo papel (miolo do nome, ou papel cravado com nome diferente).
    2) Nome diferente só em XSD, e só se existir um único papel de validação
    no cadastro (ex.: XSD do DLI). Nunca Modelo vs Contas, nem AMCC001 vs AMCC002.
    """
    atual = (nome_arquivo or "").strip()
    if not atual:
        return None
    papel = _chave_papel(atual)
    extensao = _extensao_arquivo(atual)
    outros = [
        n for n in candidatos
        if (n or "").strip() and n.strip().lower() != atual.lower()
    ]
    mesma_familia = [
        n for n in outros
        if papel and len(papel) >= 8 and _chave_papel(n) == papel
    ]
    if mesma_familia:
        return _melhor_nome(atual, mesma_familia, por_familia=True)
    if not permitir_unico_formato or not extensao:
        return None
    if extensao not in FORMATOS_NOME_NOVO_UNICO:
        return None
    mesmo_formato = [n for n in outros if _extensao_arquivo(n) == extensao]
    papeis = {_chave_papel(n) for n in mesmo_formato if _chave_papel(n)}
    if len(papeis) != 1:
        return None
    return _melhor_nome(atual, mesmo_formato, por_familia=False)


def _nome_no_site_mudou(nome_atual: str, nome_anterior: str) -> bool:
    return _familia_nome_arquivo(nome_atual) != _familia_nome_arquivo(nome_anterior)


def _frase_arquivo_novo_comparado(nome_atual: str, nome_anterior: str) -> str:
    if _nome_no_site_mudou(nome_atual, nome_anterior):
        return (
            f"Arquivo novo na página. O nome no site mudou. "
            f"Comparamos com {nome_anterior}, o último deste mesmo tipo neste cadastro, "
            "só para você ver o que mudou. "
        )
    return (
        f"Arquivo novo na página. Comparamos com {nome_anterior} "
        "para você ver o que mudou. "
    )


def _rotulo_comparado_com(nome_anterior: str, *, nome_atual: str) -> str:
    extra = " · nome no site mudou" if _nome_no_site_mudou(nome_atual, nome_anterior) else ""
    return f"[Comparado com a versão anterior{extra} · antes: {nome_anterior}] "


def _buscar_caminho_versao_parente(
    *,
    nome_arquivo: str,
    leiaute_id: Optional[int],
    excluir_arquivo_id: Optional[int] = None,
    conn: Any = None,
) -> Optional[tuple[str, str, int]]:
    """Retorna (caminho_arquivo, nome_anterior, versao_id) da versão 'irmã' mais próxima."""
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

    def _resolver(rows) -> Optional[tuple[str, str, int]]:
        disponiveis: list[tuple[str, str, int]] = []
        for row in rows:
            nome_ant = row["nome_arquivo"] or ""
            path = _resolver_caminho_armazenado(str(row["caminho_arquivo"] or ""))
            if path is None or not nome_ant.strip():
                continue
            disponiveis.append((nome_ant, str(path), int(row["versao_id"])))
        escolhido = escolher_nome_versao_parente(
            nome_arquivo,
            [n for n, _, _ in disponiveis],
            permitir_unico_formato=leiaute_id is not None,
        )
        if not escolhido:
            return None
        alvo = escolhido.strip().lower()
        for nome_ant, caminho, versao_id in disponiveis:
            if nome_ant.strip().lower() == alvo:
                return caminho, nome_ant, versao_id
        return None

    if conn is not None:
        rows = conn.execute(sql, params).fetchall()
        return _resolver(rows)

    init_db()
    with conectar() as c:
        rows = c.execute(sql, params).fetchall()
        return _resolver(rows)


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
                            _rotulo_comparado_com(
                                nome_anterior_parente, nome_atual=nome_arquivo
                            )
                            + texto
                        )
                    if tipo_comparacao == "sem_anterior":
                        return f"[Arquivo novo] {texto}"
                    return f"[Mesmo arquivo] {texto}"

                if tem_diff_conteudo and comparacao:
                    if tipo_comparacao == "versao_pareada" and nome_anterior_parente:
                        resumo = _com_rotulo(
                            _frase_arquivo_novo_comparado(
                                nome_arquivo, nome_anterior_parente
                            )
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
                            _frase_arquivo_novo_comparado(
                                nome_arquivo, nome_anterior_parente
                            )
                            + "Não apareceu diferença relevante no conteúdo."
                        )
                        impacto = (
                            "Olhe o Antes/Depois mesmo assim. "
                            + (
                                "O nome no site mudou; comparamos com o último deste mesmo tipo neste cadastro."
                                if _nome_no_site_mudou(nome_arquivo, nome_anterior_parente)
                                else "É a versão anterior do mesmo documento."
                            )
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
                            "Ainda não há outro arquivo do mesmo tipo neste leiaute para comparar."
                        )
                        impacto = (
                            "Quando existir um arquivo anterior do mesmo tipo, "
                            "o robô compara para você ver o que mudou."
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


def reprocessar_alteracoes_arquivo_novo(execucao_id: int) -> int:
    """Completa Antes/Depois de arquivo novo que ainda não tinha versão anterior."""
    if comparar_arquivos is None:
        return 0
    init_db()
    atualizados = 0
    with conectar() as conn:
        rows = conn.execute(
            """
            SELECT
                a.id,
                a.arquivo_id,
                ar.nome_arquivo,
                ar.leiaute_id,
                ar.tipo_arquivo,
                va.caminho_arquivo
            FROM alteracoes_detectadas a
            JOIN arquivos_monitorados ar ON ar.id = a.arquivo_id
            JOIN versoes_arquivos va ON va.id = a.versao_atual_id
            WHERE a.execucao_id = ?
              AND (
                a.resumo_executivo LIKE '[Sem anterior]%'
                OR a.resumo_executivo LIKE '[Arquivo novo]%'
              )
            """,
            (execucao_id,),
        ).fetchall()
        for row in rows:
            if row["leiaute_id"] is None:
                continue
            parente = _buscar_caminho_versao_parente(
                nome_arquivo=row["nome_arquivo"],
                leiaute_id=int(row["leiaute_id"]),
                excluir_arquivo_id=int(row["arquivo_id"]),
                conn=conn,
            )
            if not parente:
                continue
            caminho_ant, nome_ant, versao_ant_id = parente
            try:
                comparacao = comparar_arquivos(
                    caminho_anterior=caminho_ant,
                    caminho_atual=row["caminho_arquivo"],
                    tipo_arquivo=row["tipo_arquivo"],
                )
            except Exception as exc:
                comparacao = {
                    "resumo_executivo": (
                        f"Arquivo alterado, mas o diff automático falhou: {exc}"
                    ),
                    "impacto_sugerido": "Revisar manualmente o arquivo anexo.",
                    "itens_incluidos": [],
                    "itens_removidos": [],
                    "itens_alterados": [],
                }
            resumo_cmp = str((comparacao or {}).get("resumo_executivo") or "")
            tem_diff = bool(
                comparacao
                and (
                    (comparacao.get("itens_incluidos") or [])
                    or (comparacao.get("itens_removidos") or [])
                    or (comparacao.get("itens_alterados") or [])
                )
                and "nenhuma diferença" not in resumo_cmp.lower()
                and "nenhuma diferenca" not in resumo_cmp.lower()
            )
            nome_atual = row["nome_arquivo"]
            rotulo = _rotulo_comparado_com(nome_ant, nome_atual=nome_atual)
            if tem_diff and comparacao:
                resumo = (
                    rotulo
                    + _frase_arquivo_novo_comparado(nome_atual, nome_ant)
                    + resumo_cmp
                )
                impacto = comparacao.get("impacto_sugerido") or (
                    "Revisar as diferenças Antes/Depois e o arquivo anexo."
                )
                incluidos = list(comparacao.get("itens_incluidos") or [])
                removidos = list(comparacao.get("itens_removidos") or [])
                alterados = [
                    (
                        f'Comparação: mudanca "versão pareada (URLs diferentes)"; '
                        f'antes "{nome_ant}"; '
                        f'depois "{row["nome_arquivo"]}"'
                    )
                ] + list(comparacao.get("itens_alterados") or [])
            else:
                resumo = (
                    rotulo
                    + _frase_arquivo_novo_comparado(nome_atual, nome_ant)
                    + "Não apareceu diferença relevante no conteúdo."
                )
                impacto = (
                    "Olhe o Antes/Depois mesmo assim. "
                    + (
                        "O nome no site mudou; comparamos com o último deste mesmo tipo neste cadastro."
                        if _nome_no_site_mudou(nome_atual, nome_ant)
                        else "É a versão anterior do mesmo documento."
                    )
                )
                incluidos = [f"Novo arquivo na página (pareado com {nome_ant})."]
                removidos = []
                alterados = [
                    (
                        f'Comparação: mudanca "versão pareada sem diff material"; '
                        f'antes "{nome_ant}"; '
                        f'depois "{row["nome_arquivo"]}"'
                    )
                ]
            conn.execute(
                """
                UPDATE alteracoes_detectadas
                SET versao_anterior_id = ?,
                    resumo_executivo = ?,
                    impacto_sugerido = ?,
                    itens_incluidos = ?,
                    itens_removidos = ?,
                    itens_alterados = ?
                WHERE id = ?
                """,
                (
                    versao_ant_id,
                    resumo,
                    impacto,
                    json.dumps(incluidos, ensure_ascii=False),
                    json.dumps(removidos, ensure_ascii=False),
                    json.dumps(alterados, ensure_ascii=False),
                    row["id"],
                ),
            )
            atualizados += 1
    return atualizados


def reprocessar_comparacoes_execucao(execucao_id: int) -> int:
    """Roda de novo o comparador (ex.: receita CNPJ e datas do cabeçalho no XSD)."""
    if comparar_arquivos is None:
        return 0
    init_db()
    atualizados = 0
    with conectar() as conn:
        rows = conn.execute(
            """
            SELECT
                a.id,
                a.resumo_executivo,
                ar.nome_arquivo,
                ar.tipo_arquivo,
                va.caminho_arquivo AS caminho_atual,
                vp.caminho_arquivo AS caminho_ant,
                ar_ant.nome_arquivo AS nome_ant
            FROM alteracoes_detectadas a
            JOIN arquivos_monitorados ar ON ar.id = a.arquivo_id
            JOIN versoes_arquivos va ON va.id = a.versao_atual_id
            JOIN versoes_arquivos vp ON vp.id = a.versao_anterior_id
            JOIN arquivos_monitorados ar_ant ON ar_ant.id = vp.arquivo_id
            WHERE a.execucao_id = ?
              AND a.versao_anterior_id IS NOT NULL
            """,
            (execucao_id,),
        ).fetchall()
        for row in rows:
            atual = _resolver_caminho_armazenado(str(row["caminho_atual"] or ""))
            anterior = _resolver_caminho_armazenado(str(row["caminho_ant"] or ""))
            if atual is None or anterior is None:
                print(
                    f"Comparação pulada (arquivo não encontrado no disco): "
                    f"{row['nome_arquivo']}"
                )
                continue
            try:
                comparacao = comparar_arquivos(
                    caminho_anterior=str(anterior),
                    caminho_atual=str(atual),
                    tipo_arquivo=row["tipo_arquivo"],
                )
            except Exception as exc:
                print(f"Comparação falhou em {row['nome_arquivo']}: {exc}")
                continue
            if not comparacao:
                continue
            incluidos = list(comparacao.get("itens_incluidos") or [])
            removidos = list(comparacao.get("itens_removidos") or [])
            alterados = [
                x
                for x in (comparacao.get("itens_alterados") or [])
                if "versão pareada" not in str(x).lower()
                and "versao pareada" not in str(x).lower()
            ]
            if not (incluidos or removidos or alterados):
                continue
            resumo_cmp = str(comparacao.get("resumo_executivo") or "")
            nome_ant = str(row["nome_ant"] or "")
            nome_atual = str(row["nome_arquivo"] or "")
            resumo = (
                _rotulo_comparado_com(nome_ant, nome_atual=nome_atual)
                + _frase_arquivo_novo_comparado(nome_atual, nome_ant)
                + resumo_cmp
            )
            impacto = comparacao.get("impacto_sugerido") or (
                "Revisar as diferenças Antes/Depois e o arquivo anexo."
            )
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
                    resumo,
                    impacto,
                    json.dumps(incluidos, ensure_ascii=False),
                    json.dumps(removidos, ensure_ascii=False),
                    json.dumps(alterados, ensure_ascii=False),
                    row["id"],
                ),
            )
            atualizados += 1
    return atualizados

