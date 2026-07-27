# -*- coding: utf-8 -*-
from __future__ import annotations

import difflib
import hashlib
import re
import zipfile
from datetime import date, datetime
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

RAIZ = Path(__file__).resolve().parent.parent.parent.parent


def _resolver(caminho: str | None) -> Path | None:
    if not caminho:
        return None
    path = Path(caminho)
    if not path.is_absolute():
        path = RAIZ / path
    return path


def _limitar(itens: list[str], limite: int = 80) -> list[str]:
    if len(itens) <= limite:
        return itens
    return [*itens[:limite], f"... lista completa excede {limite} item(ns)"]


def _ler_texto(path: Path) -> str:
    data = path.read_bytes()
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="ignore")


def _normalizar_linhas(texto: str) -> list[str]:
    linhas = []
    for linha in texto.splitlines():
        normalizada = re.sub(r"\s+", " ", linha).strip()
        if normalizada:
            linhas.append(normalizada)
    return linhas


def _linhas_com_numero(texto: str) -> list[tuple[int, str]]:
    linhas = []
    for numero, linha in enumerate(texto.splitlines(), start=1):
        normalizada = re.sub(r"\s+", " ", linha).strip()
        if normalizada:
            linhas.append((numero, normalizada))
    return linhas


def _formatar_trecho(valor: str, limite: int = 5000) -> str:
    valor = valor.strip()
    if len(valor) <= limite:
        return valor
    return f"{valor[:limite]}... [texto completo excede {limite} caracteres]"


def _recortar_par_diff(antes: str, depois: str, contexto: int = 50) -> tuple[str, str]:
    """Recorta só a região que mudou (+ contexto), para Antes/Depois ficar legível."""
    a = (antes or "").strip()
    b = (depois or "").strip()
    if not a and not b:
        return "—", "—"
    if a == b:
        curto = _formatar_trecho(a, 120)
        return curto, curto
    if not a:
        return "—", _formatar_trecho(b, 180)
    if not b:
        return _formatar_trecho(a, 180), "—"

    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    spans = [
        (i1, i2, j1, j2)
        for tag, i1, i2, j1, j2 in sm.get_opcodes()
        if tag != "equal"
    ]
    if not spans:
        return _formatar_trecho(a, 160), _formatar_trecho(b, 160)

    i1 = min(s[0] for s in spans)
    i2 = max(s[1] for s in spans)
    j1 = min(s[2] for s in spans)
    j2 = max(s[3] for s in spans)
    ai, aj = max(0, i1 - contexto), min(len(a), i2 + contexto)
    bi, bj = max(0, j1 - contexto), min(len(b), j2 + contexto)
    trecho_a = (("…" if ai else "") + a[ai:aj] + ("…" if aj < len(a) else ""))
    trecho_b = (("…" if bi else "") + b[bi:bj] + ("…" if bj < len(b) else ""))
    return _formatar_trecho(trecho_a, 220), _formatar_trecho(trecho_b, 220)


def _formatar_valor_planilha(valor: Any) -> str:
    if valor is None:
        return "em branco"
    if isinstance(valor, datetime):
        return valor.strftime("%d/%m/%Y %H:%M")
    if isinstance(valor, date):
        return valor.strftime("%d/%m/%Y")
    texto = str(valor).strip()
    return texto if texto else "em branco"


def _comparar_linhas(
    linhas_ant_num: list[tuple[int, str]],
    linhas_atual_num: list[tuple[int, str]],
    *,
    contexto: str = "",
) -> dict[str, list[str]]:
    linhas_ant = [linha for _, linha in linhas_ant_num]
    linhas_atual = [linha for _, linha in linhas_atual_num]
    prefixo = f"{contexto} - " if contexto else ""
    incluidos: list[str] = []
    removidos: list[str] = []
    alterados = []

    matcher = difflib.SequenceMatcher(None, linhas_ant, linhas_atual)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "insert":
            for numero, valor in linhas_atual_num[j1:j2]:
                incluidos.append(
                    f"{prefixo}linha atual {numero}: incluído \"{_formatar_trecho(valor)}\""
                )
        elif tag == "delete":
            for numero, valor in linhas_ant_num[i1:i2]:
                removidos.append(
                    f"{prefixo}linha anterior {numero}: removido \"{_formatar_trecho(valor)}\""
                )
        if tag == "replace":
            qtd = max(i2 - i1, j2 - j1)
            for idx in range(qtd):
                ant = linhas_ant_num[i1 + idx] if i1 + idx < i2 else None
                novo = linhas_atual_num[j1 + idx] if j1 + idx < j2 else None
                if ant and novo:
                    antes_c, depois_c = _recortar_par_diff(ant[1], novo[1])
                    alterados.append(
                        f"{prefixo}linha anterior {ant[0]} -> linha atual {novo[0]}: "
                        f"antes \"{antes_c}\"; depois \"{depois_c}\""
                    )
                elif novo:
                    incluidos.append(
                        f"{prefixo}linha atual {novo[0]}: incluído \"{_formatar_trecho(novo[1])}\""
                    )
                elif ant:
                    removidos.append(
                        f"{prefixo}linha anterior {ant[0]}: removido \"{_formatar_trecho(ant[1])}\""
                    )

    return {
        "incluidos": incluidos,
        "removidos": removidos,
        "alterados": alterados,
    }


def _comparar_texto(anterior: Path, atual: Path) -> dict[str, Any]:
    diff = _comparar_linhas(
        _linhas_com_numero(_ler_texto(anterior)),
        _linhas_com_numero(_ler_texto(atual)),
    )
    incluidos = diff["incluidos"]
    removidos = diff["removidos"]
    alterados = diff["alterados"]

    return {
        "resumo_executivo": _resumo(incluidos, removidos, alterados),
        "impacto_sugerido": "Revisar os trechos alterados para avaliar impacto operacional.",
        "itens_incluidos": _limitar(incluidos),
        "itens_removidos": _limitar(removidos),
        "itens_alterados": _limitar(alterados),
    }


def _xml_tag(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _xml_attr(elem: ElementTree.Element, nome: str) -> str:
    for chave, valor in elem.attrib.items():
        if _xml_tag(chave) == nome:
            return valor
    return ""


def _mapa_linhas_xsd(texto: str) -> dict[str, int]:
    linhas: dict[str, int] = {}
    for numero, linha in enumerate(texto.splitlines(), start=1):
        for nome in re.findall(r'\b(?:name|ref)="([^"]+)"', linha):
            linhas.setdefault(nome, numero)
    return linhas


def _coletar_xsd(path: Path) -> dict[str, dict[str, Any]]:
    texto = _ler_texto(path)
    root = ElementTree.fromstring(texto)
    linhas_por_nome = _mapa_linhas_xsd(texto)
    itens: dict[str, dict[str, Any]] = {}

    def walk(elem: ElementTree.Element, prefixo: str) -> None:
        tag = _xml_tag(elem.tag)
        nome = _xml_attr(elem, "name") or _xml_attr(elem, "ref") or tag
        atual = f"{prefixo}/{nome}" if prefixo else nome
        if tag in {"element", "attribute", "complexType", "simpleType"}:
            assinatura = {
                "tag": tag,
                "type": _xml_attr(elem, "type"),
                "base": _xml_attr(elem, "base"),
                "minOccurs": _xml_attr(elem, "minOccurs"),
                "maxOccurs": _xml_attr(elem, "maxOccurs"),
                "use": _xml_attr(elem, "use"),
            }
            assinatura_texto = ", ".join(
                f"{k}={v}" for k, v in assinatura.items() if v
            ) or tag
            itens[atual] = {
                "assinatura": assinatura_texto,
                "linha": linhas_por_nome.get(nome),
                "nome": nome,
            }
        for child in list(elem):
            walk(child, atual)

    walk(root, "")
    return itens


def _comparar_xsd(anterior: Path, atual: Path) -> dict[str, Any]:
    ant = _coletar_xsd(anterior)
    novo = _coletar_xsd(atual)
    ch_ant = set(ant)
    ch_novo = set(novo)
    incluidos = [
        f"Linha atual {novo[chave].get('linha') or '?'}: campo/schema incluído {chave} "
        f"({novo[chave]['assinatura']})"
        for chave in sorted(ch_novo - ch_ant)
    ]
    removidos = [
        f"Linha anterior {ant[chave].get('linha') or '?'}: campo/schema removido {chave} "
        f"({ant[chave]['assinatura']})"
        for chave in sorted(ch_ant - ch_novo)
    ]
    alterados = []
    for chave in sorted(ch_ant & ch_novo):
        if ant[chave]["assinatura"] != novo[chave]["assinatura"]:
            alterados.append(
                f"{chave}: linha anterior {ant[chave].get('linha') or '?'} -> "
                f"linha atual {novo[chave].get('linha') or '?'}; antes "
                f"({ant[chave]['assinatura']}); depois ({novo[chave]['assinatura']})"
            )
    return {
        "resumo_executivo": _resumo(incluidos, removidos, alterados),
        "impacto_sugerido": "Revisar campos, tipos e obrigatoriedade alterados no schema.",
        "itens_incluidos": _limitar(incluidos),
        "itens_removidos": _limitar(removidos),
        "itens_alterados": _limitar(alterados),
    }


def _comparar_xlsx(anterior: Path, atual: Path) -> dict[str, Any]:
    try:
        import openpyxl  # type: ignore
    except Exception:
        return _fallback_dependencia("XLSX", "openpyxl")

    from openpyxl.utils import get_column_letter

    # read_only=False: max_row/max_column refletem melhor a área usada;
    # data_only=False: evita recalcular fórmulas (mais rápido e estável no servidor).
    wb_ant = openpyxl.load_workbook(anterior, data_only=False, read_only=False)
    wb_atual = openpyxl.load_workbook(atual, data_only=False, read_only=False)
    abas_ant = set(wb_ant.sheetnames)
    abas_atual = set(wb_atual.sheetnames)

    incluidos = [f"Aba incluída: {aba}" for aba in sorted(abas_atual - abas_ant)]
    removidos = [f"Aba removida: {aba}" for aba in sorted(abas_ant - abas_atual)]
    alterados: list[str] = []
    limite_evidencias = 50

    for aba in sorted(abas_ant & abas_atual):
        if len(alterados) >= limite_evidencias:
            break
        ws_ant = wb_ant[aba]
        ws_atual = wb_atual[aba]
        # Compara por linhas (valores) em vez de célula a célula com .cell() —
        # muito mais rápido em planilhas grandes do Bacen.
        rows_ant = list(ws_ant.iter_rows(values_only=True))
        rows_atual = list(ws_atual.iter_rows(values_only=True))
        max_row = max(len(rows_ant), len(rows_atual))
        cabecalhos = rows_atual[0] if rows_atual else ()

        for row_idx in range(max_row):
            if len(alterados) >= limite_evidencias:
                break
            row_ant = rows_ant[row_idx] if row_idx < len(rows_ant) else ()
            row_atual = rows_atual[row_idx] if row_idx < len(rows_atual) else ()
            max_col = max(len(row_ant), len(row_atual))
            for col_idx in range(max_col):
                v_ant = row_ant[col_idx] if col_idx < len(row_ant) else None
                v_atual = row_atual[col_idx] if col_idx < len(row_atual) else None
                if v_ant == v_atual:
                    continue
                coluna = get_column_letter(col_idx + 1)
                cabecalho = cabecalhos[col_idx] if col_idx < len(cabecalhos) else None
                contexto = f", coluna {cabecalho}" if cabecalho and row_idx != 0 else ""
                alterados.append(
                    f"Aba {aba}, célula {coluna}{row_idx + 1}{contexto}: "
                    f'antes "{_formatar_valor_planilha(v_ant)}"; '
                    f'depois "{_formatar_valor_planilha(v_atual)}"'
                )
                if len(alterados) >= limite_evidencias:
                    break

    wb_ant.close()
    wb_atual.close()

    return {
        "resumo_executivo": _resumo(incluidos, removidos, alterados),
        "impacto_sugerido": "Revisar abas e células alteradas antes de atualizar rotinas internas.",
        "itens_incluidos": _limitar(incluidos),
        "itens_removidos": _limitar(removidos),
        "itens_alterados": _limitar(alterados),
    }


def _coluna_excel(col_zero_based: int) -> str:
    col = col_zero_based + 1
    letras = ""
    while col:
        col, resto = divmod(col - 1, 26)
        letras = chr(65 + resto) + letras
    return letras


def _comparar_xls(anterior: Path, atual: Path) -> dict[str, Any]:
    try:
        import xlrd  # type: ignore
    except Exception:
        return _fallback_dependencia("XLS", "xlrd")

    wb_ant = xlrd.open_workbook(str(anterior))
    wb_atual = xlrd.open_workbook(str(atual))
    abas_ant = set(wb_ant.sheet_names())
    abas_atual = set(wb_atual.sheet_names())
    incluidos = [f"Aba incluída: {aba}" for aba in sorted(abas_atual - abas_ant)]
    removidos = [f"Aba removida: {aba}" for aba in sorted(abas_ant - abas_atual)]
    alterados: list[str] = []

    for aba in sorted(abas_ant & abas_atual):
        sh_ant = wb_ant.sheet_by_name(aba)
        sh_atual = wb_atual.sheet_by_name(aba)
        max_row = max(sh_ant.nrows, sh_atual.nrows)
        max_col = max(sh_ant.ncols, sh_atual.ncols)
        for row in range(max_row):
            for col in range(max_col):
                v_ant = sh_ant.cell_value(row, col) if row < sh_ant.nrows and col < sh_ant.ncols else None
                v_atual = sh_atual.cell_value(row, col) if row < sh_atual.nrows and col < sh_atual.ncols else None
                if v_ant != v_atual:
                    coluna = _coluna_excel(col)
                    cabecalho = (
                        sh_atual.cell_value(0, col)
                        if row != 0 and sh_atual.nrows and col < sh_atual.ncols
                        else ""
                    )
                    contexto = f", coluna {cabecalho}" if cabecalho else ""
                    alterados.append(
                        f"Aba {aba}, célula {coluna}{row + 1}{contexto}: "
                        f'antes "{_formatar_valor_planilha(v_ant)}"; '
                        f'depois "{_formatar_valor_planilha(v_atual)}"'
                    )
                    if len(alterados) >= 200:
                        break
            if len(alterados) >= 200:
                break

    return {
        "resumo_executivo": _resumo(incluidos, removidos, alterados),
        "impacto_sugerido": "Revisar abas e células alteradas antes de atualizar rotinas internas.",
        "itens_incluidos": _limitar(incluidos),
        "itens_removidos": _limitar(removidos),
        "itens_alterados": _limitar(alterados),
    }


def _comparar_pdf(anterior: Path, atual: Path) -> dict[str, Any]:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception:
        return _fallback_dependencia("PDF", "pypdf")

    def extrair_paginas(path: Path) -> list[list[tuple[int, str]]]:
        reader = PdfReader(str(path))
        paginas = []
        for page in reader.pages:
            paginas.append(_linhas_com_numero(page.extract_text() or ""))
        return paginas

    # Ruído típico de cabeçalho/rodapé em PDF do Bacen — não ajuda o gestor.
    ruido = {"interno", "confidencial", "página", "pagina"}

    paginas_ant = extrair_paginas(anterior)
    paginas_atual = extrair_paginas(atual)
    incluidos: list[str] = []
    removidos: list[str] = []
    alterados: list[str] = []
    total_paginas = max(len(paginas_ant), len(paginas_atual))
    for idx in range(total_paginas):
        ant = paginas_ant[idx] if idx < len(paginas_ant) else []
        novo = paginas_atual[idx] if idx < len(paginas_atual) else []
        diff = _comparar_linhas(ant, novo, contexto=f"Página {idx + 1}")
        for item in diff["incluidos"]:
            trecho = item.rsplit(': incluído "', 1)[-1].rstrip('"').strip().lower()
            if trecho in ruido or len(trecho) <= 2:
                continue
            incluidos.append(item)
        for item in diff["removidos"]:
            trecho = item.rsplit(': removido "', 1)[-1].rstrip('"').strip().lower()
            if trecho in ruido or len(trecho) <= 2:
                continue
            removidos.append(item)
        for item in diff["alterados"]:
            # Descarta "mudança" em que o recorte ficou idêntico (só ruído de layout).
            if ': antes "' in item and '"; depois "' in item:
                try:
                    meio = item.split(': antes "', 1)[1]
                    ant_t, dep_t = meio.rsplit('"; depois "', 1)
                    dep_t = dep_t.rstrip('"')
                    if ant_t.strip() == dep_t.strip():
                        continue
                except Exception:
                    pass
            alterados.append(item)

    return {
        "resumo_executivo": _resumo(incluidos, removidos, alterados),
        "impacto_sugerido": "Revisar as páginas e linhas alteradas no PDF.",
        "itens_incluidos": _limitar(incluidos),
        "itens_removidos": _limitar(removidos),
        "itens_alterados": _limitar(alterados),
    }


def _comparar_zip(anterior: Path, atual: Path) -> dict[str, Any]:
    with zipfile.ZipFile(anterior) as z_ant, zipfile.ZipFile(atual) as z_atual:
        ant_infos = {i.filename: i for i in z_ant.infolist()}
        novo_infos = {i.filename: i for i in z_atual.infolist()}
        ant = set(ant_infos)
        novo = set(novo_infos)
        incluidos = []
        removidos = []
        alterados = []

        for nome in sorted(novo - ant):
            data = z_atual.read(nome)
            evidencia = _evidencia_zip_texto(data)
            incluidos.append(
                f"Arquivo interno incluído: {nome} ({len(data)} bytes){evidencia}"
            )
        for nome in sorted(ant - novo):
            data = z_ant.read(nome)
            evidencia = _evidencia_zip_texto(data)
            removidos.append(
                f"Arquivo interno removido: {nome} ({len(data)} bytes){evidencia}"
            )
        for nome in sorted(ant & novo):
            data_ant = z_ant.read(nome)
            data_novo = z_atual.read(nome)
            if hashlib.sha256(data_ant).hexdigest() != hashlib.sha256(data_novo).hexdigest():
                if _parece_texto(nome):
                    diff = _comparar_linhas(
                        _linhas_com_numero(_bytes_para_texto(data_ant)),
                        _linhas_com_numero(_bytes_para_texto(data_novo)),
                        contexto=f"Arquivo interno {nome}",
                    )
                    alterados.extend(diff["alterados"])
                    incluidos.extend(diff["incluidos"])
                    removidos.extend(diff["removidos"])
                else:
                    alterados.append(
                        f"Arquivo interno {nome}: conteúdo binário alterado; "
                        f"tamanho anterior {len(data_ant)} bytes; tamanho atual {len(data_novo)} bytes"
                    )
    return {
        "resumo_executivo": _resumo(incluidos, removidos, alterados),
        "impacto_sugerido": "Revisar arquivos internos alterados no pacote ZIP.",
        "itens_incluidos": _limitar(incluidos),
        "itens_removidos": _limitar(removidos),
        "itens_alterados": _limitar(alterados),
    }


def _bytes_para_texto(data: bytes) -> str:
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="ignore")


def _parece_texto(nome: str) -> bool:
    return Path(nome).suffix.lower() in {
        ".txt",
        ".csv",
        ".xml",
        ".xsd",
        ".json",
        ".html",
        ".htm",
    }


def _evidencia_zip_texto(data: bytes) -> str:
    texto = _bytes_para_texto(data)
    linhas = _normalizar_linhas(texto)
    if not linhas:
        return ""
    return f"; evidência: \"{_formatar_trecho(linhas[0], 180)}\""


def _fallback_dependencia(tipo: str, pacote: str) -> dict[str, Any]:
    return {
        "resumo_executivo": (
            f"Arquivo {tipo} alterado. A extração detalhada requer a dependência {pacote}."
        ),
        "impacto_sugerido": f"Instalar {pacote} para comparar conteúdo {tipo} em detalhe.",
        "itens_incluidos": [],
        "itens_removidos": [],
        "itens_alterados": [f"Comparação detalhada pendente: dependência {pacote} ausente."],
    }


def _resumo(incluidos: list[str], removidos: list[str], alterados: list[str]) -> str:
    total = len(incluidos) + len(removidos) + len(alterados)
    if total == 0:
        return "Nenhuma diferença textual/estrutural relevante foi identificada."
    return (
        f"Foram identificadas {len(incluidos)} inclusão(ões), "
        f"{len(removidos)} remoção(ões) e {len(alterados)} alteração(ões)."
    )


def comparar_arquivos(
    *,
    caminho_anterior: str | None,
    caminho_atual: str | None,
    tipo_arquivo: str,
) -> dict[str, Any] | None:
    anterior = _resolver(caminho_anterior)
    atual = _resolver(caminho_atual)
    if not anterior or not atual or not anterior.exists() or not atual.exists():
        return None

    tipo = tipo_arquivo.lower().lstrip(".")
    try:
        if tipo == "xsd":
            return _comparar_xsd(anterior, atual)
        if tipo in {"xml", "txt", "csv", "json", "html", "htm"}:
            return _comparar_texto(anterior, atual)
        if tipo in {"xlsx", "xlsm"}:
            return _comparar_xlsx(anterior, atual)
        if tipo == "xls":
            return _comparar_xls(anterior, atual)
        if tipo == "pdf":
            return _comparar_pdf(anterior, atual)
        if tipo == "zip":
            return _comparar_zip(anterior, atual)
    except Exception as exc:
        return {
            "resumo_executivo": f"Falha ao comparar conteúdo do arquivo: {exc}",
            "impacto_sugerido": "Revisar manualmente o arquivo alterado.",
            "itens_incluidos": [],
            "itens_removidos": [],
            "itens_alterados": [str(exc)],
        }
    return _comparar_texto(anterior, atual)
