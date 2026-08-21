# -*- coding: utf-8 -*-
"""Planilha única do comunicado — linguagem simples (e-mail e Exportar)."""
from __future__ import annotations

from dataclasses import dataclass, field
from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

BLUE = "2E3192"
BLUE_SOFT = "EEF0FA"
TEXT = "1F2937"
MUTED = "64748B"
GRAY = "F8F9FA"
GREEN_SOFT = "E8F7EE"
YELLOW_SOFT = "FFF8E6"
ROW_ALT = "F3F4F8"
WHITE = "FFFFFF"
BORDER = "E5E7EB"
LINK = "1D4ED8"

# Linhas fixas em todas as abas
ROW_TITULO = 1
ROW_EXPLICACAO = 2
ROW_CABECALHO = 4
ROW_DADOS = 5


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


def _borda() -> Border:
    lado = Side(style="thin", color=BORDER)
    return Border(left=lado, right=lado, top=lado, bottom=lado)


def _escrever_topo(ws: Worksheet, n_cols: int, titulo: str, explicacao: str) -> None:
    ultima = get_column_letter(n_cols)
    ws.merge_cells(f"A{ROW_TITULO}:{ultima}{ROW_TITULO}")
    ws.merge_cells(f"A{ROW_EXPLICACAO}:{ultima}{ROW_EXPLICACAO}")

    c1 = ws.cell(row=ROW_TITULO, column=1, value=titulo)
    c1.font = Font(name="Arial", size=16, bold=True, color=BLUE)
    c1.alignment = Alignment(vertical="center", wrap_text=True)
    c1.fill = PatternFill("solid", fgColor=BLUE_SOFT)
    ws.row_dimensions[ROW_TITULO].height = 30

    c2 = ws.cell(row=ROW_EXPLICACAO, column=1, value=explicacao)
    c2.font = Font(name="Arial", size=10, color=MUTED)
    c2.alignment = Alignment(vertical="center", wrap_text=True)
    c2.fill = PatternFill("solid", fgColor=GRAY)
    ws.row_dimensions[ROW_EXPLICACAO].height = 48

    ws.row_dimensions[3].height = 10


def _escrever_cabecalho(ws: Worksheet, colunas: list[str]) -> None:
    for col, nome in enumerate(colunas, start=1):
        cell = ws.cell(row=ROW_CABECALHO, column=col, value=nome)
        cell.fill = PatternFill("solid", fgColor=BLUE)
        cell.font = Font(name="Arial", bold=True, color=WHITE, size=10)
        cell.alignment = Alignment(vertical="center", horizontal="center", wrap_text=True)
        cell.border = _borda()
    ws.row_dimensions[ROW_CABECALHO].height = 38


def _estilo_dado(cell, *, horizontal: str = "left", fill: str | None = None) -> None:
    cell.font = Font(name="Arial", size=10, color=TEXT)
    cell.alignment = Alignment(vertical="top", horizontal=horizontal, wrap_text=True)
    cell.border = _borda()
    if fill:
        cell.fill = PatternFill("solid", fgColor=fill)


def _link(cell) -> None:
    if not cell.value:
        return
    cell.hyperlink = str(cell.value)
    cell.font = Font(name="Arial", size=10, color=LINK, underline="single")
    cell.alignment = Alignment(vertical="top", horizontal="left", wrap_text=True)
    cell.border = _borda()


def _larguras(ws: Worksheet, widths: dict[str, float]) -> None:
    for col, width in widths.items():
        ws.column_dimensions[col].width = width


def _fechar_aba(ws: Worksheet, n_cols: int, altura_dados: int = 56) -> None:
    ultima = get_column_letter(n_cols)
    fim = max(ROW_CABECALHO, ws.max_row)
    ws.auto_filter.ref = f"A{ROW_CABECALHO}:{ultima}{fim}"
    ws.freeze_panes = f"A{ROW_DADOS}"
    ws.sheet_view.showGridLines = False
    for row_idx in range(ROW_DADOS, ws.max_row + 1):
        ws.row_dimensions[row_idx].height = altura_dados


def _escrever_linha(ws: Worksheet, row: int, valores: list) -> None:
    for col, valor in enumerate(valores, start=1):
        ws.cell(row=row, column=col, value=valor)


def gerar_bytes_planilha_gestor(
    dados: DadosPlanilhaGestor,
    *,
    nome_arquivo: str,
) -> tuple[bytes, str]:
    """
    Três abas com título explicativo e formatação legível:
    Resumo · O que mudou · Só aviso
    """
    wb = Workbook()

    # --- Resumo ---
    ws = wb.active
    ws.title = "Resumo"
    cols = [
        "Data",
        "Leiaute",
        "Arquivo",
        "Situação",
        "Precisa agir?",
        "Quantidade de mudanças",
        "Link Bacen",
    ]
    _escrever_topo(
        ws,
        len(cols),
        "Resumo — visão geral dos arquivos",
        (
            "Aqui você vê um arquivo por linha. "
            "Use a coluna “Precisa agir?” para saber o que revisar. "
            "“Sim” = houve mudança de conteúdo. “Não” = o Bacen só republicou no site."
        ),
    )
    _escrever_cabecalho(ws, cols)

    row = ROW_DADOS
    linhas_resumo: list[list] = []
    for arq in dados.arquivos_agir:
        linhas_resumo.append(
            [arq.data, arq.leiaute, arq.arquivo, arq.situacao, "Sim", arq.qtd_mudancas, arq.link]
        )
    for arq in dados.arquivos_aviso:
        linhas_resumo.append(
            [arq.data, arq.leiaute, arq.arquivo, arq.situacao, "Não", 0, arq.link]
        )
    if not linhas_resumo:
        linhas_resumo.append(
            ["", "", "", "Nenhuma mudança nesta exportação.", "", "", ""]
        )

    for i, valores in enumerate(linhas_resumo):
        _escrever_linha(ws, row, valores)
        zebra = ROW_ALT if i % 2 == 1 else None
        for col in range(1, len(cols) + 1):
            cell = ws.cell(row=row, column=col)
            fill = zebra
            horizontal = "left"
            if col == 5:
                horizontal = "center"
                if cell.value == "Sim":
                    fill = GREEN_SOFT
                elif cell.value == "Não":
                    fill = YELLOW_SOFT
            elif col == 6:
                horizontal = "center"
            _estilo_dado(cell, horizontal=horizontal, fill=fill)
        _link(ws.cell(row=row, column=7))
        row += 1

    _larguras(ws, {"A": 18, "B": 12, "C": 34, "D": 28, "E": 14, "F": 14, "G": 36})
    _fechar_aba(ws, len(cols), altura_dados=56)

    # --- O que mudou ---
    ws = wb.create_sheet("O que mudou")
    cols = [
        "Data",
        "Leiaute",
        "Arquivo",
        "Onde",
        "O que mudou",
        "Antes",
        "Depois",
        "O que fazer",
    ]
    _escrever_topo(
        ws,
        len(cols),
        "O que mudou — detalhe das diferenças",
        (
            "Cada linha é uma mudança. "
            "Veja onde está (aba, célula ou página), o que mudou, o valor de antes e o de depois, "
            "e o que fazer na rotina."
        ),
    )
    _escrever_cabecalho(ws, cols)

    row = ROW_DADOS
    linhas = list(dados.linhas_mudanca)
    if not linhas:
        _escrever_linha(
            ws,
            row,
            ["", "", "", "", "Nenhuma diferença detalhada nesta exportação.", "", "", ""],
        )
        for col in range(1, len(cols) + 1):
            _estilo_dado(ws.cell(row=row, column=col))
    else:
        for i, lin in enumerate(linhas):
            _escrever_linha(
                ws,
                row,
                [
                    lin.data,
                    lin.leiaute,
                    lin.arquivo,
                    lin.onde,
                    lin.o_que_mudou,
                    lin.antes,
                    lin.depois,
                    lin.o_que_fazer,
                ],
            )
            fill = ROW_ALT if i % 2 == 1 else None
            for col in range(1, len(cols) + 1):
                _estilo_dado(ws.cell(row=row, column=col), fill=fill)
            row += 1

    _larguras(
        ws,
        {"A": 16, "B": 12, "C": 28, "D": 22, "E": 22, "F": 32, "G": 32, "H": 36},
    )
    _fechar_aba(ws, len(cols), altura_dados=68)

    # --- Só aviso ---
    ws = wb.create_sheet("Só aviso")
    cols = ["Data", "Leiaute", "Arquivo", "Observação", "Link Bacen"]
    _escrever_topo(
        ws,
        len(cols),
        "Só aviso — sem ação de conteúdo",
        (
            "Nestes arquivos o Bacen republicou no site, mas o texto, a célula ou a tabela "
            "não mudaram. Em geral não exige ajuste de rotina — só fique ciente."
        ),
    )
    _escrever_cabecalho(ws, cols)

    row = ROW_DADOS
    avisos = list(dados.arquivos_aviso)
    if not avisos:
        _escrever_linha(
            ws,
            row,
            ["", "", "", "Nenhum arquivo só de aviso nesta exportação.", ""],
        )
        for col in range(1, len(cols) + 1):
            _estilo_dado(ws.cell(row=row, column=col))
    else:
        for i, arq in enumerate(avisos):
            _escrever_linha(
                ws,
                row,
                [
                    arq.data,
                    arq.leiaute,
                    arq.arquivo,
                    arq.observacao
                    or "O Bacen republicou o arquivo no site, sem mudança de conteúdo.",
                    arq.link,
                ],
            )
            fill = ROW_ALT if i % 2 == 1 else None
            for col in range(1, 5):
                _estilo_dado(ws.cell(row=row, column=col), fill=fill)
            _estilo_dado(ws.cell(row=row, column=5), fill=fill)
            _link(ws.cell(row=row, column=5))
            row += 1

    _larguras(ws, {"A": 18, "B": 12, "C": 34, "D": 55, "E": 36})
    _fechar_aba(ws, len(cols), altura_dados=56)

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
