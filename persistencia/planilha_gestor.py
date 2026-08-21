# -*- coding: utf-8 -*-
"""Planilha única do comunicado — linguagem simples (e-mail e Exportar)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from io import BytesIO
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

BLUE = "2E3192"
TEXT = "1F2937"
GRAY = "F8F9FA"


@dataclass
class ArquivoResumoPlanilha:
    data: str
    leiaute: str
    arquivo: str
    situacao: str
    precisa_agir: bool
    qtd_mudancas: int
    link: str
    observacao: str = ""


@dataclass
class LinhaMudancaPlanilha:
    data: str
    leiaute: str
    arquivo: str
    onde: str
    o_que_mudou: str
    antes: str
    depois: str
    o_que_fazer: str


@dataclass
class DadosPlanilhaGestor:
    arquivos_agir: list[ArquivoResumoPlanilha] = field(default_factory=list)
    linhas_mudanca: list[LinhaMudancaPlanilha] = field(default_factory=list)
    arquivos_aviso: list[ArquivoResumoPlanilha] = field(default_factory=list)


def _estilo_cabecalho(ws, n_cols: int) -> None:
    fill = PatternFill("solid", fgColor=BLUE)
    font = Font(name="Arial", bold=True, color="FFFFFF", size=10)
    for col in range(1, n_cols + 1):
        cell = ws.cell(row=1, column=col)
        cell.fill = fill
        cell.font = font
        cell.alignment = Alignment(vertical="center", wrap_text=True, horizontal="center")


def _estilo_dados(ws) -> None:
    border = Border(bottom=Side(style="thin", color="E5E7EB"))
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.font = Font(name="Arial", size=10, color=TEXT)
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            cell.border = border


def _larguras(ws, widths: dict[str, float]) -> None:
    for col, width in widths.items():
        ws.column_dimensions[col].width = width


def _filtro_e_freeze(ws, n_cols: int) -> None:
    if ws.max_row < 1:
        return
    ultima = get_column_letter(n_cols)
    ws.auto_filter.ref = f"A1:{ultima}{ws.max_row}"
    ws.freeze_panes = "A2"


def gerar_bytes_planilha_gestor(
    dados: DadosPlanilhaGestor,
    *,
    nome_arquivo: str,
) -> tuple[bytes, str]:
    """
    Três abas intuitivas:
    1) Resumo — um arquivo por linha
    2) O que mudou — cada diferença
    3) Só aviso — republicação sem mudança de conteúdo (se houver)
    """
    wb = Workbook()

    # --- Resumo ---
    ws_resumo = wb.active
    ws_resumo.title = "Resumo"
    cab_resumo = [
        "Data",
        "Leiaute",
        "Arquivo",
        "Situação",
        "Precisa agir?",
        "Quantidade de mudanças",
        "Link Bacen",
    ]
    ws_resumo.append(cab_resumo)
    for arq in dados.arquivos_agir:
        ws_resumo.append(
            [
                arq.data,
                arq.leiaute,
                arq.arquivo,
                arq.situacao,
                "Sim",
                arq.qtd_mudancas,
                arq.link,
            ]
        )
    for arq in dados.arquivos_aviso:
        ws_resumo.append(
            [
                arq.data,
                arq.leiaute,
                arq.arquivo,
                arq.situacao,
                "Não",
                0,
                arq.link,
            ]
        )
    _estilo_cabecalho(ws_resumo, len(cab_resumo))
    _estilo_dados(ws_resumo)
    _larguras(
        ws_resumo,
        {"A": 18, "B": 14, "C": 42, "D": 36, "E": 14, "F": 22, "G": 40},
    )
    _filtro_e_freeze(ws_resumo, len(cab_resumo))
    for row in range(2, ws_resumo.max_row + 1):
        cell = ws_resumo.cell(row=row, column=7)
        if cell.value:
            cell.hyperlink = str(cell.value)
            cell.style = "Hyperlink"

    # --- O que mudou ---
    ws_det = wb.create_sheet("O que mudou")
    cab_det = [
        "Data",
        "Leiaute",
        "Arquivo",
        "Onde",
        "O que mudou",
        "Antes",
        "Depois",
        "O que fazer",
    ]
    ws_det.append(cab_det)
    for lin in dados.linhas_mudanca:
        ws_det.append(
            [
                lin.data,
                lin.leiaute,
                lin.arquivo,
                lin.onde,
                lin.o_que_mudou,
                lin.antes,
                lin.depois,
                lin.o_que_fazer,
            ]
        )
    _estilo_cabecalho(ws_det, len(cab_det))
    _estilo_dados(ws_det)
    _larguras(
        ws_det,
        {
            "A": 18,
            "B": 14,
            "C": 36,
            "D": 28,
            "E": 28,
            "F": 40,
            "G": 40,
            "H": 44,
        },
    )
    _filtro_e_freeze(ws_det, len(cab_det))

    # --- Só aviso ---
    ws_aviso = wb.create_sheet("Só aviso")
    cab_aviso = ["Data", "Leiaute", "Arquivo", "Observação", "Link Bacen"]
    ws_aviso.append(cab_aviso)
    if dados.arquivos_aviso:
        for arq in dados.arquivos_aviso:
            ws_aviso.append(
                [
                    arq.data,
                    arq.leiaute,
                    arq.arquivo,
                    arq.observacao
                    or "O Bacen republicou o arquivo no site, sem mudança de conteúdo.",
                    arq.link,
                ]
            )
    else:
        ws_aviso.append(
            [
                "",
                "",
                "",
                "Nenhum arquivo só de aviso nesta exportação.",
                "",
            ]
        )
    _estilo_cabecalho(ws_aviso, len(cab_aviso))
    _estilo_dados(ws_aviso)
    _larguras(ws_aviso, {"A": 18, "B": 14, "C": 42, "D": 56, "E": 40})
    _filtro_e_freeze(ws_aviso, len(cab_aviso))
    for row in range(2, ws_aviso.max_row + 1):
        cell = ws_aviso.cell(row=row, column=5)
        if cell.value:
            cell.hyperlink = str(cell.value)
            cell.style = "Hyperlink"

    # Nota no rodapé visual: aba Resumo com fundo cinza na linha vazia se nada
    if ws_resumo.max_row == 1:
        ws_resumo.append(
            [
                "",
                "",
                "",
                "Nenhuma mudança nesta exportação.",
                "",
                "",
                "",
            ]
        )
        for cell in ws_resumo[2]:
            cell.fill = PatternFill("solid", fgColor=GRAY)

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue(), nome_arquivo


def rotulo_situacao(codigo: str) -> str:
    mapa = {
        "versao_pareada": "Arquivo novo na página",
        "sem_anterior": "Arquivo novo sem versão anterior",
        "mesmo_arquivo": "Mesmo arquivo atualizado",
        "aviso": "Republicado no site (sem mudança de conteúdo)",
    }
    return mapa.get(codigo, "Arquivo atualizado")
