# -*- coding: utf-8 -*-
from __future__ import annotations

import difflib
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


def _limitar(itens: list[str], limite: int = 30) -> list[str]:
    if len(itens) <= limite:
        return itens
    return [*itens[:limite], f"... mais {len(itens) - limite} item(ns)"]


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


def _comparar_texto(anterior: Path, atual: Path) -> dict[str, Any]:
    linhas_ant = _normalizar_linhas(_ler_texto(anterior))
    linhas_atual = _normalizar_linhas(_ler_texto(atual))
    diff = list(difflib.ndiff(linhas_ant, linhas_atual))
    incluidos = [d[2:] for d in diff if d.startswith("+ ")]
    removidos = [d[2:] for d in diff if d.startswith("- ")]
    alterados = []

    matcher = difflib.SequenceMatcher(None, linhas_ant, linhas_atual)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "replace":
            antes = " | ".join(linhas_ant[i1:i2])[:500]
            depois = " | ".join(linhas_atual[j1:j2])[:500]
            alterados.append(f"Antes: {antes} -> Depois: {depois}")

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


def _coletar_xsd(path: Path) -> dict[str, str]:
    root = ElementTree.fromstring(_ler_texto(path))
    itens: dict[str, str] = {}

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
            itens[atual] = ", ".join(
                f"{k}={v}" for k, v in assinatura.items() if v
            ) or tag
        for child in list(elem):
            walk(child, atual)

    walk(root, "")
    return itens


def _comparar_xsd(anterior: Path, atual: Path) -> dict[str, Any]:
    ant = _coletar_xsd(anterior)
    novo = _coletar_xsd(atual)
    ch_ant = set(ant)
    ch_novo = set(novo)
    incluidos = [f"{chave}: {novo[chave]}" for chave in sorted(ch_novo - ch_ant)]
    removidos = [f"{chave}: {ant[chave]}" for chave in sorted(ch_ant - ch_novo)]
    alterados = [
        f"{chave}: {ant[chave]} -> {novo[chave]}"
        for chave in sorted(ch_ant & ch_novo)
        if ant[chave] != novo[chave]
    ]
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
                    alterados.append(
                        f"{aba}!{row},{col}: {v_ant!r} -> {v_atual!r}"
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

    def extrair(path: Path) -> str:
        reader = PdfReader(str(path))
        partes = []
        for page in reader.pages:
            partes.append(page.extract_text() or "")
        return "\n".join(partes)

    ant_txt = anterior.with_suffix(anterior.suffix + ".txt")
    atual_txt = atual.with_suffix(atual.suffix + ".txt")
    ant_txt.write_text(extrair(anterior), encoding="utf-8")
    atual_txt.write_text(extrair(atual), encoding="utf-8")
    return _comparar_texto(ant_txt, atual_txt)


def _comparar_zip(anterior: Path, atual: Path) -> dict[str, Any]:
    with zipfile.ZipFile(anterior) as z_ant, zipfile.ZipFile(atual) as z_atual:
        ant = {i.filename: i.file_size for i in z_ant.infolist()}
        novo = {i.filename: i.file_size for i in z_atual.infolist()}
    incluidos = [f"{k} ({novo[k]} bytes)" for k in sorted(set(novo) - set(ant))]
    removidos = [f"{k} ({ant[k]} bytes)" for k in sorted(set(ant) - set(novo))]
    alterados = [
        f"{k}: {ant[k]} bytes -> {novo[k]} bytes"
        for k in sorted(set(ant) & set(novo))
        if ant[k] != novo[k]
    ]
    return {
        "resumo_executivo": _resumo(incluidos, removidos, alterados),
        "impacto_sugerido": "Revisar arquivos internos alterados no pacote ZIP.",
        "itens_incluidos": _limitar(incluidos),
        "itens_removidos": _limitar(removidos),
        "itens_alterados": _limitar(alterados),
    }


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
        if tipo in {"xsd", "xml"}:
            return _comparar_xsd(anterior, atual)
        if tipo in {"txt", "csv", "json", "html", "htm"}:
            return _comparar_texto(anterior, atual)
        if tipo in {"xlsx", "xlsm"}:
            return _comparar_xlsx(anterior, atual)
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
