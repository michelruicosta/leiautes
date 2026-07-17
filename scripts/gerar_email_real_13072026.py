# -*- coding: utf-8 -*-
"""Monta o novo modelo de e-mail usando o envio real de 13/07/2026."""
from __future__ import annotations

import html
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from backend.app.services.comparador_arquivos import comparar_arquivos
from persistencia.db import conectar
from scripts.verifica_leiautes_finaud import BLUE_BRAND, gerar_html_email, _html_lista_diferencas


SAIDA = BASE / "prototipos" / "email_real_13072026_novo_modelo.html"

COMPARACOES = [
    {
        "titulo": "DLI-2062 - 2062-202607-v9-vi16-Instruções de Preenchimento.pdf",
        "tipo": "pdf",
        "atual": "2062-202607-v9-vi16-Instruções de Preenchimento.pdf",
        "anterior": "2062-202509-v3-vi4-Instruções de Preenchimento.pdf",
        "link": "https://www.bcb.gov.br/content/estabilidadefinanceira/Leiaute2062/Atual/informacoes_tecnicas/2062-202607-v9-vi16-Instru%C3%A7%C3%B5es%20de%20Preenchimento.pdf",
    },
    {
        "titulo": "DLI-2062 - 2062-202607-v1-vi1-Modelo documento (contas).xlsx",
        "tipo": "xlsx",
        "atual": "2062-202607-v1-vi1-Modelo documento (contas).xlsx",
        "anterior": "2062-202505-v1-Modelo documento (contas).xlsx",
        "link": "https://www.bcb.gov.br/content/estabilidadefinanceira/Leiaute2062/Atual/informacoes_tecnicas/2062-202607-v1-vi1-Modelo%20documento%20(contas).xlsx",
    },
    {
        "titulo": "DLI-2062 - 2062-202505-v1-Modelo documento (contas).xlsx",
        "tipo": "xlsx",
        "atual": "2062-202505-v1-Modelo documento (contas).xlsx",
        "anterior": "2062 - 202411-v1-Modelo documento (contas).xlsx",
        "link": "https://www.bcb.gov.br/content/estabilidadefinanceira/Leiaute2062/Atual/informacoes_tecnicas/2062-202505-v1-Modelo%20documento%20(contas).xlsx",
    },
]


def _path_por_nome(nome: str) -> str:
    with conectar() as conn:
        row = conn.execute(
            """
            SELECT v.caminho_arquivo
            FROM arquivos_monitorados ar
            JOIN versoes_arquivos v ON v.id = ar.ultima_versao_id
            WHERE ar.nome_arquivo = ?
            ORDER BY v.id DESC
            LIMIT 1
            """,
            (nome,),
        ).fetchone()
    if not row:
        raise RuntimeError(f"Arquivo não encontrado no histórico: {nome}")
    return row["caminho_arquivo"]


def _card(item: dict) -> str:
    comparacao = comparar_arquivos(
        caminho_anterior=_path_por_nome(item["anterior"]),
        caminho_atual=_path_por_nome(item["atual"]),
        tipo_arquivo=item["tipo"],
    ) or {
        "resumo_executivo": "Arquivo detectado, mas não foi possível comparar conteúdo.",
        "impacto_sugerido": "Revisar manualmente o arquivo alterado.",
        "itens_incluidos": [],
        "itens_alterados": [],
        "itens_removidos": [],
    }
    return f"""
    <div class="change-card">
      <p class="change-title">{html.escape(item["titulo"])} <span class="muted">({html.escape(item["tipo"])})</span></p>
      <p><a href="{html.escape(item["link"])}" target="_blank" style="color:{BLUE_BRAND}; text-decoration:none;">Abrir arquivo no Bacen</a></p>
      <p>{html.escape(comparacao["resumo_executivo"])}</p>
      <p class="muted">{html.escape(comparacao["impacto_sugerido"])}</p>
      {_html_lista_diferencas("Entrou", "entrou", comparacao.get("itens_incluidos", []), "Nenhuma inclusão identificada.")}
      {_html_lista_diferencas("Mudou", "mudou", comparacao.get("itens_alterados", []), "Nenhuma alteração de conteúdo identificada.")}
      {_html_lista_diferencas("Saiu", "saiu", comparacao.get("itens_removidos", []), "Nenhuma remoção identificada.")}
    </div>
    """


def gerar() -> Path:
    resumo = """
    <p style="font-size:17px; line-height:1.55;">
      Foram identificadas possíveis atualizações na data de <strong>13/07/2026</strong>.
    </p>
    <p style="font-size:15px; line-height:1.55; color:#5b6b84;">
      No modelo anterior, o e-mail listava apenas os 3 anexos. No modelo abaixo,
      o gestor já recebe o resumo do que entrou, mudou e saiu em cada arquivo.
    </p>
    <p style="font-size:17px;"><strong style="color:#2e3192;">Arquivo(s) encontrado(s):</strong></p>
    """
    html_final = gerar_html_email(
        resumo + "".join(_card(item) for item in COMPARACOES),
        "13/07/2026",
        "logo-finaud",
    )
    html_final = html_final.replace(
        '<img src="cid:logo-finaud" alt="FINAUD TEC" style="max-width:220px; height:auto;">',
        '<div style="font-size:42px;font-weight:bold;color:#2e3192;">finaud</div>',
    )
    html_final = html_final.replace(
        "<title></title>",
        "<title>Atenção: Atualização na página de Leiautes do Bacen na data: 13/07/2026</title>",
    )
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(html_final, encoding="utf-8")
    return SAIDA


if __name__ == "__main__":
    print(gerar())
