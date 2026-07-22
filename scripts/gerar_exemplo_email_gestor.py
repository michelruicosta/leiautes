# -*- coding: utf-8 -*-
"""Gera um HTML de exemplo do e-mail do gestor com alterações reais do banco."""
from __future__ import annotations

import argparse
import html
import json
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from persistencia.db import conectar
from scripts.verifica_leiautes_finaud import BLUE_BRAND, gerar_html_email, _html_lista_diferencas


def _lista(valor: str | None) -> list[str]:
    if not valor:
        return []
    parsed = json.loads(valor)
    return parsed if isinstance(parsed, list) else []


def _alteracoes(execucao_id: int, limite: int = 3) -> list[dict]:
    with conectar() as conn:
        rows = conn.execute(
            """
            SELECT
                a.id,
                COALESCE(l.codigo, '') AS leiaute_codigo,
                ar.nome_arquivo,
                ar.tipo_arquivo,
                ar.final_url,
                a.resumo_executivo,
                a.impacto_sugerido,
                a.itens_incluidos,
                a.itens_removidos,
                a.itens_alterados
            FROM alteracoes_detectadas a
            JOIN arquivos_monitorados ar ON ar.id = a.arquivo_id
            LEFT JOIN leiautes_monitorados l ON l.id = ar.leiaute_id
            WHERE a.execucao_id = ?
            ORDER BY a.id DESC
            LIMIT ?
            """,
            (execucao_id, limite),
        ).fetchall()
    itens = []
    for row in rows:
        data = dict(row)
        data["itens_incluidos"] = _lista(data["itens_incluidos"])
        data["itens_removidos"] = _lista(data["itens_removidos"])
        data["itens_alterados"] = _lista(data["itens_alterados"])
        itens.append(data)
    return itens


def _card(alteracao: dict) -> str:
    titulo = html.escape(
        f"{alteracao['leiaute_codigo'] or 'Leiaute'} - {alteracao['nome_arquivo']}"
    )
    tipo = html.escape(alteracao["tipo_arquivo"])
    link = html.escape(alteracao.get("final_url") or "#")
    return f"""
    <div class="change-card">
      <p class="change-title">{titulo} <span class="muted">({tipo})</span></p>
      <p><a href="{link}" target="_blank" style="color:{BLUE_BRAND}; text-decoration:none;">Abrir arquivo monitorado</a></p>
      <p>{html.escape(alteracao['resumo_executivo'])}</p>
      <p class="muted">{html.escape(alteracao['impacto_sugerido'])}</p>
      {_html_lista_diferencas("Entrou", "entrou", alteracao["itens_incluidos"], "Nenhuma inclusao identificada.")}
      {_html_lista_diferencas("Mudou", "mudou", alteracao["itens_alterados"], "Nenhuma alteracao de conteudo identificada.")}
      {_html_lista_diferencas("Saiu", "saiu", alteracao["itens_removidos"], "Nenhuma remocao identificada.")}
    </div>
    """


def gerar(execucao_id: int, saida: Path) -> Path:
    alteracoes = _alteracoes(execucao_id)
    data_ref = datetime.now().strftime("%d/%m/%Y")
    resumo = f"""
    <p style="font-size:17px; line-height:1.55;">
      Foram identificadas <strong>{len(alteracoes)} alteração(ões) principais</strong>
      nos leiautes monitorados. Abaixo está o resumo executivo com o que entrou,
      o que mudou e o que saiu.
    </p>
    <p style="font-size:15px; color:#5b6b84;">
      Este exemplo foi gerado com dados reais da execução {execucao_id}.
    </p>
    """
    html_final = gerar_html_email(
        resumo + "".join(_card(alt) for alt in alteracoes),
        data_ref,
        "logo-finaud",
    )
    html_final = html_final.replace(
        '<img src="cid:logo-finaud" alt="FINAUD TEC" style="max-width:220px; height:auto;">',
        '<div style="font-size:42px;font-weight:bold;color:#2e3192;">finaud</div>',
    )
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(html_final, encoding="utf-8")
    return saida


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execucao-id", type=int, default=11)
    parser.add_argument(
        "--saida",
        type=Path,
        default=BASE / "prototipos" / "email_gestor_exemplo_mudancas.html",
    )
    args = parser.parse_args()
    print(gerar(args.execucao_id, args.saida))


if __name__ == "__main__":
    main()
