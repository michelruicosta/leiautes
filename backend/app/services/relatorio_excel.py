# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime
from io import BytesIO
from typing import Any

from openpyxl import Workbook
from openpyxl.cell.cell import Cell
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

from persistencia.db import conectar, init_db

BLUE = "2E3192"
GREEN = "DFF3E6"
YELLOW = "FFF0C2"
RED = "FDE2E1"
GRAY = "EEF2F7"
TEXT = "1F2937"


def _json_list(valor: str | None) -> list[str]:
    if not valor:
        return []
    try:
        parsed = json.loads(valor)
        return parsed if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        return []


def _fmt_data(valor: str | None) -> str:
    if not valor:
        return ""
    try:
        return datetime.fromisoformat(valor).strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return valor


def _parse_evidencia(texto: str, tipo: str) -> dict[str, str]:
    texto = str(texto or "").strip()
    padroes = [
        r'^(.*?): antes "([\s\S]*)"; depois "([\s\S]*)"$',
        r"^(.*?): antes ([\s\S]*); depois ([\s\S]*)$",
        r"^(.*?): (linha anterior.*?); antes \(([\s\S]*)\); depois \(([\s\S]*)\)$",
    ]
    for padrao in padroes:
        match = re.match(padrao, texto)
        if not match:
            continue
        if len(match.groups()) == 4:
            return {
                "local": f"{match.group(1)} - {match.group(2)}",
                "antes": match.group(3),
                "depois": match.group(4),
            }
        return {"local": match.group(1), "antes": match.group(2), "depois": match.group(3)}

    incluido = re.match(r'^(.*?): incluído "([\s\S]*)"$', texto)
    if incluido:
        return {"local": incluido.group(1), "antes": "", "depois": incluido.group(2)}
    removido = re.match(r'^(.*?): removido "([\s\S]*)"$', texto)
    if removido:
        return {"local": removido.group(1), "antes": removido.group(2), "depois": ""}
    interno = re.match(r'^Arquivo interno incluído: ([^;]+); evidência: "([\s\S]*)"$', texto)
    if interno:
        return {"local": f"Arquivo interno {interno.group(1)}", "antes": "", "depois": interno.group(2)}

    if tipo == "Saiu":
        return {"local": "Evidência", "antes": texto, "depois": ""}
    return {"local": "Evidência", "antes": "", "depois": texto}


def _buscar_alteracoes(escopo: str) -> tuple[list[dict[str, Any]], str]:
    init_db()
    where = ""
    params: list[Any] = []
    titulo = "Histórico completo de alterações"

    with conectar() as conn:
        if escopo == "ultima":
            row = conn.execute(
                """
                SELECT execucao_id
                FROM alteracoes_detectadas
                ORDER BY execucao_id DESC, id DESC
                LIMIT 1
                """
            ).fetchone()
            if row:
                where = "WHERE a.execucao_id = ?"
                params.append(row["execucao_id"])
                titulo = f"Alterações da execução {row['execucao_id']}"

        rows = conn.execute(
            f"""
            SELECT
                a.id,
                a.execucao_id,
                a.status,
                a.criado_em,
                a.resumo_executivo,
                a.impacto_sugerido,
                a.itens_incluidos,
                a.itens_removidos,
                a.itens_alterados,
                COALESCE(l.codigo, '') AS leiaute_codigo,
                COALESCE(l.nome, '') AS leiaute_nome,
                ar.nome_arquivo,
                ar.tipo_arquivo,
                ar.url,
                ar.final_url,
                e.iniciado_em,
                e.finalizado_em,
                va.caminho_arquivo AS versao_anterior,
                vn.caminho_arquivo AS versao_atual,
                va.tamanho_bytes AS tamanho_anterior,
                vn.tamanho_bytes AS tamanho_atual
            FROM alteracoes_detectadas a
            JOIN arquivos_monitorados ar ON ar.id = a.arquivo_id
            LEFT JOIN leiautes_monitorados l ON l.id = ar.leiaute_id
            LEFT JOIN execucoes e ON e.id = a.execucao_id
            LEFT JOIN versoes_arquivos va ON va.id = a.versao_anterior_id
            LEFT JOIN versoes_arquivos vn ON vn.id = a.versao_atual_id
            {where}
            ORDER BY a.execucao_id DESC, a.id DESC
            """,
            params,
        ).fetchall()

    alteracoes = []
    for row in rows:
        item = dict(row)
        item["itens_incluidos"] = _json_list(item.get("itens_incluidos"))
        item["itens_removidos"] = _json_list(item.get("itens_removidos"))
        item["itens_alterados"] = _json_list(item.get("itens_alterados"))
        alteracoes.append(item)
    return alteracoes, titulo


def _append(ws, values: list[Any], fill: str | None = None, bold: bool = False) -> None:
    ws.append(values)
    for cell in ws[ws.max_row]:
        cell.alignment = Alignment(vertical="top", wrap_text=True)
        cell.font = Font(name="Arial", size=10, bold=bold, color=TEXT)
        cell.border = Border(bottom=Side(style="thin", color="E5E7EB"))
        if fill:
            cell.fill = PatternFill("solid", fgColor=fill)


def _titulo(ws, texto: str, subtitulo: str) -> None:
    ws["A1"] = texto
    ws["A1"].font = Font(name="Arial", size=18, bold=True, color=BLUE)
    ws["A2"] = subtitulo
    ws["A2"].font = Font(name="Arial", size=10, color="64748B")
    ws.merge_cells("A1:H1")
    ws.merge_cells("A2:H2")


def _tabela(ws, nome: str, primeira_linha: int, ultima_coluna: int) -> None:
    if ws.max_row <= primeira_linha:
        return
    ref = f"A{primeira_linha}:{get_column_letter(ultima_coluna)}{ws.max_row}"
    table = Table(displayName=nome, ref=ref)
    table.tableStyleInfo = TableStyleInfo(
        name="TableStyleMedium2",
        showFirstColumn=False,
        showLastColumn=False,
        showRowStripes=True,
        showColumnStripes=False,
    )
    ws.add_table(table)
    ws.freeze_panes = f"A{primeira_linha + 1}"
    ws.auto_filter.ref = ref


def _ajustar(ws, larguras: dict[str, int]) -> None:
    for col, largura in larguras.items():
        ws.column_dimensions[col].width = largura
    for row in ws.iter_rows():
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=True)
    ws.sheet_view.showGridLines = False


def _metric_cell(cell: Cell, fill: str) -> None:
    cell.fill = PatternFill("solid", fgColor=fill)
    cell.font = Font(name="Arial", size=14, bold=True, color=TEXT)
    cell.alignment = Alignment(horizontal="center", vertical="center")
    cell.border = Border(
        left=Side(style="thin", color="D8DEE8"),
        right=Side(style="thin", color="D8DEE8"),
        top=Side(style="thin", color="D8DEE8"),
        bottom=Side(style="thin", color="D8DEE8"),
    )


def gerar_relatorio_alteracoes_xlsx(escopo: str = "historico") -> tuple[bytes, str]:
    escopo = "ultima" if escopo == "ultima" else "historico"
    alteracoes, titulo = _buscar_alteracoes(escopo)
    wb = Workbook()
    ws_resumo = wb.active
    ws_resumo.title = "Resumo executivo"
    ws_mudancas = wb.create_sheet("Mudanças")
    ws_arquivo = wb.create_sheet("Por arquivo")
    ws_anexos = wb.create_sheet("Anexos")
    ws_criterios = wb.create_sheet("Critérios")

    linhas_mudancas: list[list[Any]] = []
    cont_tipo = Counter()
    cont_arquivo = Counter()
    for alt in alteracoes:
        for tipo, itens in [
            ("Entrou", alt["itens_incluidos"]),
            ("Mudou", alt["itens_alterados"]),
            ("Saiu", alt["itens_removidos"]),
        ]:
            cont_tipo[tipo] += len(itens)
            for texto in itens:
                parsed = _parse_evidencia(texto, tipo)
                linhas_mudancas.append(
                    [
                        alt["execucao_id"],
                        _fmt_data(alt["criado_em"]),
                        alt["leiaute_codigo"],
                        alt["nome_arquivo"],
                        alt["tipo_arquivo"],
                        tipo,
                        parsed["local"],
                        parsed["antes"],
                        parsed["depois"],
                        alt["impacto_sugerido"],
                        alt["status"],
                        alt["final_url"] or alt["url"],
                    ]
                )
        cont_arquivo[(alt["leiaute_codigo"], alt["nome_arquivo"], alt["tipo_arquivo"])] += (
            len(alt["itens_incluidos"]) + len(alt["itens_alterados"]) + len(alt["itens_removidos"])
        )

    _titulo(
        ws_resumo,
        titulo,
        f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')} | Fonte: banco do app Leiautes",
    )
    for label_cell, value_cell, label, value, fill in [
        ("A4", "B4", "Arquivos", len(alteracoes), GRAY),
        ("C4", "D4", "Entrou", cont_tipo["Entrou"], GREEN),
        ("E4", "F4", "Mudou", cont_tipo["Mudou"], YELLOW),
        ("G4", "H4", "Saiu", cont_tipo["Saiu"], RED),
    ]:
        ws_resumo[label_cell] = label
        ws_resumo[value_cell] = value
        ws_resumo[label_cell].font = Font(name="Arial", bold=True, color=BLUE)
        ws_resumo[label_cell].alignment = Alignment(horizontal="center", vertical="center")
        _metric_cell(ws_resumo[value_cell], fill)

    _append(ws_resumo, ["Leiaute", "Arquivo", "Tipo", "Total de evidências"], fill=BLUE, bold=True)
    resumo_header_row = ws_resumo.max_row
    for cell in ws_resumo[resumo_header_row]:
        cell.font = Font(name="Arial", bold=True, color="FFFFFF")
    for (leiaute, arquivo, tipo), total in cont_arquivo.most_common(12):
        _append(ws_resumo, [leiaute, arquivo, tipo, total])
    _tabela(ws_resumo, "TabelaResumoArquivos", resumo_header_row, 4)
    _ajustar(ws_resumo, {"A": 18, "B": 58, "C": 12, "D": 18, "E": 12, "F": 12, "G": 12, "H": 12})

    cab = [
        "Execução",
        "Data",
        "Leiaute",
        "Arquivo",
        "Tipo arquivo",
        "Tipo mudança",
        "Local / evidência",
        "Antes",
        "Depois",
        "Impacto sugerido",
        "Status",
        "Link Bacen",
    ]
    _append(ws_mudancas, cab, fill=BLUE, bold=True)
    for cell in ws_mudancas[1]:
        cell.font = Font(name="Arial", bold=True, color="FFFFFF")
    for linha in linhas_mudancas:
        fill = GREEN if linha[5] == "Entrou" else YELLOW if linha[5] == "Mudou" else RED
        _append(ws_mudancas, linha, fill=fill)
        link_cell = ws_mudancas.cell(row=ws_mudancas.max_row, column=12)
        if link_cell.value:
            link_cell.hyperlink = str(link_cell.value)
            link_cell.style = "Hyperlink"
    _tabela(ws_mudancas, "TabelaMudancas", 1, len(cab))
    _ajustar(ws_mudancas, {"A": 10, "B": 18, "C": 14, "D": 46, "E": 12, "F": 14, "G": 34, "H": 48, "I": 48, "J": 38, "K": 14, "L": 32})

    _append(ws_arquivo, ["Leiaute", "Arquivo", "Tipo", "Entrou", "Mudou", "Saiu", "Resumo", "Impacto"], fill=BLUE, bold=True)
    for cell in ws_arquivo[1]:
        cell.font = Font(name="Arial", bold=True, color="FFFFFF")
    for alt in alteracoes:
        _append(
            ws_arquivo,
            [
                alt["leiaute_codigo"],
                alt["nome_arquivo"],
                alt["tipo_arquivo"],
                len(alt["itens_incluidos"]),
                len(alt["itens_alterados"]),
                len(alt["itens_removidos"]),
                alt["resumo_executivo"],
                alt["impacto_sugerido"],
            ],
        )
    _tabela(ws_arquivo, "TabelaPorArquivo", 1, 8)
    _ajustar(ws_arquivo, {"A": 14, "B": 52, "C": 12, "D": 10, "E": 10, "F": 10, "G": 42, "H": 42})

    _append(
        ws_anexos,
        ["Execução", "Leiaute", "Arquivo", "Tipo", "Versão anterior", "Versão atual", "Tamanho anterior", "Tamanho atual", "Link Bacen"],
        fill=BLUE,
        bold=True,
    )
    for cell in ws_anexos[1]:
        cell.font = Font(name="Arial", bold=True, color="FFFFFF")
    for alt in alteracoes:
        _append(
            ws_anexos,
            [
                alt["execucao_id"],
                alt["leiaute_codigo"],
                alt["nome_arquivo"],
                alt["tipo_arquivo"],
                alt["versao_anterior"] or "",
                alt["versao_atual"] or "",
                alt["tamanho_anterior"] or "",
                alt["tamanho_atual"] or "",
                alt["final_url"] or alt["url"],
            ],
        )
        link_cell = ws_anexos.cell(row=ws_anexos.max_row, column=9)
        if link_cell.value:
            link_cell.hyperlink = str(link_cell.value)
            link_cell.style = "Hyperlink"
    _tabela(ws_anexos, "TabelaAnexos", 1, 9)
    _ajustar(ws_anexos, {"A": 10, "B": 14, "C": 48, "D": 10, "E": 48, "F": 48, "G": 16, "H": 16, "I": 42})

    for idx, linha in enumerate(
        [
            ["Campo", "Valor"],
            ["Escopo", "Última execução com alteração" if escopo == "ultima" else "Histórico completo"],
            ["Geração", datetime.now().strftime("%d/%m/%Y %H:%M")],
            ["Fonte", "Banco SQLite do aplicativo Leiautes"],
            ["Tipos de evidência", "Entrou, Mudou, Saiu"],
            ["Observação", "A planilha histórica é gerada sob demanda e reflete os dados gravados até o momento."],
        ],
        start=1,
    ):
        _append(ws_criterios, linha, fill=BLUE if idx == 1 else None, bold=idx == 1)
        if idx == 1:
            for cell in ws_criterios[idx]:
                cell.font = Font(name="Arial", bold=True, color="FFFFFF")
    _tabela(ws_criterios, "TabelaCriterios", 1, 2)
    _ajustar(ws_criterios, {"A": 24, "B": 90})

    buffer = BytesIO()
    wb.save(buffer)
    sufixo = "envio" if escopo == "ultima" else "historico"
    nome = f"relatorio_alteracoes_leiautes_{sufixo}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    return buffer.getvalue(), nome
