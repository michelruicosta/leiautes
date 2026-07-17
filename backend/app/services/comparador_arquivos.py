# -*- coding: utf-8 -*-
from __future__ import annotations

import difflib
import hashlib
import re
import zipfile
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


def _limitar(itens: list[str], limite: int = 500) -> list[str]:
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
                    alterados.append(
                        f"{prefixo}linha anterior {ant[0]} -> linha atual {novo[0]}: "
                        f"antes \"{_formatar_trecho(ant[1])}\"; depois \"{_formatar_trecho(novo[1])}\""
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

    wb_ant = openpyxl.load_workbook(anterior, data_only=True, read_only=True)
    wb_atual = openpyxl.load_workbook(atual, data_only=True, read_only=True)
    abas_ant = set(wb_ant.sheetnames)
    abas_atual = set(wb_atual.sheetnames)
    from openpyxl.utils import get_column_letter

    incluidos = [f"Aba incluída: {aba}" for aba in sorted(abas_atual - abas_ant)]
    removidos = [f"Aba removida: {aba}" for aba in sorted(abas_ant - abas_atual)]
    alterados: list[str] = []

    for aba in sorted(abas_ant & abas_atual):
        ws_ant = wb_ant[aba]
        ws_atual = wb_atual[aba]
        max_row = max(ws_ant.max_row or 0, ws_atual.max_row or 0)
        max_col = max(ws_ant.max_column or 0, ws_atual.max_column or 0)
        for row in range(1, max_row + 1):
            for col in range(1, max_col + 1):
                v_ant = ws_ant.cell(row=row, column=col).value
                v_atual = ws_atual.cell(row=row, column=col).value
                if v_ant != v_atual:
                    coluna = get_column_letter(col)
                    cabecalho = ws_atual.cell(row=1, column=col).value
                    contexto = f", coluna {cabecalho}" if cabecalho and row != 1 else ""
                    alterados.append(
                        f"Aba {aba}, célula {coluna}{row}{contexto}: "
                        f"antes {v_ant!r}; depois {v_atual!r}"
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
                        f"antes {v_ant!r}; depois {v_atual!r}"
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
        incluidos.extend(diff["incluidos"])
        removidos.extend(diff["removidos"])
        alterados.extend(diff["alterados"])

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
