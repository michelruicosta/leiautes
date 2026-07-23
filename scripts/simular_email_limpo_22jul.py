# -*- coding: utf-8 -*-
"""Simula e-mail limpo com os 14 arquivos do alerta de 22/07/2026 (só michel@)."""
from __future__ import annotations

import os
import smtplib
import sys
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import make_msgid
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

os.environ.setdefault("LEIAUTES_EMAIL_TEST_TO", "michel@finaud.com.br")

import importlib.util

_spec = importlib.util.spec_from_file_location(
    "verifica_leiautes_finaud",
    BASE / "scripts" / "verifica_leiautes_finaud.py",
)
_motor = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_motor)

BLUE_BRAND = _motor.BLUE_BRAND
CONFIG_PATH = _motor.CONFIG_PATH
LOGO_PATH = _motor.LOGO_PATH
gerar_html_email = _motor.gerar_html_email
load_email_config = _motor.load_email_config
montar_corpo_email_alteracoes = _motor.montar_corpo_email_alteracoes

# Arquivos do e-mail antigo de 22/07 (DLO /Atual/).
# Evidências ilustrativas — o dia 22 no robô antigo foi por metadados;
# aqui mostramos como o e-mail limpo ficaria com diffs de conteúdo típicos.
ARQUIVOS_22JUL = [
    {
        "nome": "2061-202607-v7-vi8 - Instruções de Preenchimento.pdf",
        "tipo": "pdf",
        "url": "https://www.bcb.gov.br/content/estabilidadefinanceira/Leiautes2061/Atual/informacoes_tecnicas/2061-202607-v7-vi8%20-%20Instru%C3%A7%C3%B5es%20de%20Preenchimento.pdf",
        "mudou": [
            'Página 3, linha atual 12: antes "prazo de envio D+2"; depois "prazo de envio D+1"',
            'Página 5, linha atual 4: antes "versão vi7"; depois "versão vi8"',
        ],
        "entrou": [],
        "saiu": [],
    },
    {
        "nome": "2061-202509-v7-vi7 - Instruções de Preenchimento.pdf",
        "tipo": "pdf",
        "url": "https://www.bcb.gov.br/content/estabilidadefinanceira/Leiautes2061/Atual/informacoes_tecnicas/2061-202509-v7-vi7%20-%20Instru%C3%A7%C3%B5es%20de%20Preenchimento.pdf",
        "mudou": [
            'Página 2, linha atual 8: antes "campo opcional"; depois "campo obrigatório"',
        ],
        "entrou": [],
        "saiu": [],
    },
    {
        "nome": "2061-202607-v1-vi1-Leiaute do DLO.xlsx",
        "tipo": "xlsx",
        "url": "https://www.bcb.gov.br/content/estabilidadefinanceira/Leiautes2061/Atual/informacoes_tecnicas/2061-202607-v1-vi1-Leiaute%20do%20DLO.xlsx",
        "mudou": [
            'Aba Leiaute, célula B12, coluna Domínio: antes "1;2"; depois "1;2;3"',
            'Aba Leiaute, célula C18, coluna Descrição: antes "Saldo contábil"; depois "Saldo contábil diário"',
            'Aba Dominios, célula A4: antes "em branco"; depois "3 - Novo domínio"',
        ],
        "entrou": ['Aba Dominios: incluído "linha domínio 3"'],
        "saiu": [],
    },
    {
        "nome": "2061-202509-v2-vi2-Leiaute do DLO.xlsx",
        "tipo": "xlsx",
        "url": "https://www.bcb.gov.br/content/estabilidadefinanceira/Leiautes2061/Atual/informacoes_tecnicas/2061-202509-v2-vi2-Leiaute%20do%20DLO.xlsx",
        "mudou": [
            'Aba Leiaute, célula D9: antes "N"; depois "S"',
        ],
        "entrou": [],
        "saiu": [],
    },
    {
        "nome": "2061-202508-v2-vi4-Leiaute do DLO.xlsx",
        "tipo": "xlsx",
        "url": "https://www.bcb.gov.br/content/estabilidadefinanceira/Leiautes2061/Atual/informacoes_tecnicas/2061-202508-v2-vi4-Leiaute%20do%20DLO.xlsx",
        "mudou": [
            'Aba Leiaute, célula E22: antes "10"; depois "12"',
        ],
        "entrou": [],
        "saiu": [],
    },
    {
        "nome": "2061-202607-v1-vi1-Modelo documento (contas).xlsx",
        "tipo": "xlsx",
        "url": "https://www.bcb.gov.br/content/estabilidadefinanceira/Leiautes2061/Atual/informacoes_tecnicas/2061-202607-v1-vi1-Modelo%20documento%20(contas).xlsx",
        "mudou": [
            'Aba Modelo, célula A1: antes "Modelo v1"; depois "Modelo v1-vi1"',
        ],
        "entrou": [],
        "saiu": ['Aba Legado: removido "coluna auxiliar X"'],
    },
    {
        "nome": "2061-202509-v3-vi3-Modelo documento (contas).xlsx",
        "tipo": "xlsx",
        "url": "https://www.bcb.gov.br/content/estabilidadefinanceira/Leiautes2061/Atual/informacoes_tecnicas/2061-202509-v3-vi3-Modelo%20documento%20(contas).xlsx",
        "mudou": [
            'Aba Modelo, célula B3: antes "conta sintética"; depois "conta analítica"',
        ],
        "entrou": [],
        "saiu": [],
    },
    {
        "nome": "2061-202508-v3-vi3-Modelo documento (contas).xlsx",
        "tipo": "xlsx",
        "url": "https://www.bcb.gov.br/content/estabilidadefinanceira/Leiautes2061/Atual/informacoes_tecnicas/2061-202508-v3-vi3-Modelo%20documento%20(contas).xlsx",
        "mudou": [
            'Aba Modelo, célula C5: antes "0"; depois "1"',
        ],
        "entrou": [],
        "saiu": [],
    },
    {
        "nome": "2061-202607-v2-Planilha de configuração.xlsx",
        "tipo": "xlsx",
        "url": "https://www.bcb.gov.br/content/estabilidadefinanceira/Leiautes2061/Atual/informacoes_tecnicas/2061-202607-v2-Planilha%20de%20configura%C3%A7%C3%A3o.xlsx",
        "mudou": [
            'Aba Config, célula A2: antes "parametro_old"; depois "parametro_new"',
            'Aba Config, célula B2: antes "false"; depois "true"',
        ],
        "entrou": [],
        "saiu": [],
    },
    {
        "nome": "2061-202601-v3-Planilha de configuração.xlsx",
        "tipo": "xlsx",
        "url": "https://www.bcb.gov.br/content/estabilidadefinanceira/Leiautes2061/Atual/informacoes_tecnicas/2061-202601-v3-Planilha%20de%20configura%C3%A7%C3%A3o.xlsx",
        "mudou": [
            'Aba Config, célula A8: antes "v2"; depois "v3"',
        ],
        "entrou": [],
        "saiu": [],
    },
    {
        "nome": "2061-202510-v1-Planilha de configuração.xlsx",
        "tipo": "xlsx",
        "url": "https://www.bcb.gov.br/content/estabilidadefinanceira/Leiautes2061/Atual/informacoes_tecnicas/2061-202510-v1-Planilha%20de%20configura%C3%A7%C3%A3o.xlsx",
        "mudou": [
            'Aba Config, célula C1: antes "em branco"; depois "ativo"',
        ],
        "entrou": [],
        "saiu": [],
    },
    {
        "nome": "2061-202411-v3-Críticas de pós processamento.xlsx",
        "tipo": "xlsx",
        "url": "https://www.bcb.gov.br/content/estabilidadefinanceira/Leiautes2061/Atual/informacoes_tecnicas/2061-202411-v3-Cr%C3%ADticas%20de%20p%C3%B3s%20processamento.xlsx",
        "mudou": [
            'Aba Criticas, célula A15: antes "C001"; depois "C001A"',
        ],
        "entrou": ['Aba Criticas: incluído "C099 - Nova crítica"'],
        "saiu": [],
    },
    {
        "nome": "2061-202407-v1-Críticas de pós processamento.xlsx",
        "tipo": "xlsx",
        "url": "https://www.bcb.gov.br/content/estabilidadefinanceira/Leiautes2061/Atual/informacoes_tecnicas/2061-202407-v1-Cr%C3%ADticas%20de%20p%C3%B3s%20processamento.xlsx",
        "mudou": [
            'Aba Criticas, célula B3: antes "bloqueante=N"; depois "bloqueante=S"',
        ],
        "entrou": [],
        "saiu": [],
    },
    {
        "nome": "Críticas de Pós-Processamento DLO_2061_V5 Ajustada.xlsx",
        "tipo": "xlsx",
        "url": "https://www.bcb.gov.br/content/estabilidadefinanceira/Leiautes2061/Atual/informacoes_tecnicas/Cr%C3%ADticas%20de%20P%C3%B3s-Processamento%20DLO_2061_V5%20Ajustada.xlsx",
        "mudou": [
            'Aba Criticas, célula A1: antes "V4"; depois "V5 Ajustada"',
            'Aba Criticas, célula D10: antes "msg antiga"; depois "msg revisada"',
            'Aba Criticas, célula E10: antes "1"; depois "2"',
            'Aba Criticas, célula F10: antes "ok"; depois "revisar"',
            'Aba Criticas, célula G10: antes "em branco"; depois "obs"',
            'Aba Criticas, célula H10: antes "em branco"; depois "extra"',
        ],
        "entrou": [],
        "saiu": [],
    },
]


def main() -> None:
    alterados = []
    detalhes = {}
    for arq in ARQUIVOS_22JUL:
        url = arq["url"]
        alterados.append({"url": url, "evidencia": "etag mudou, last_modified mudou"})
        n_in, n_out, n_ch = len(arq["entrou"]), len(arq["saiu"]), len(arq["mudou"])
        detalhes[url] = {
            "leiaute_codigo": "DLO-2061",
            "nome_arquivo": arq["nome"],
            "tipo_arquivo": arq["tipo"],
            "resumo_executivo": (
                f"Foram identificadas {n_in} inclusão(ões), "
                f"{n_out} remoção(ões) e {n_ch} alteração(ões)."
            ),
            "impacto_sugerido": "Revisar o arquivo antes de atualizar rotinas internas.",
            "itens_incluidos": arq["entrou"],
            "itens_removidos": arq["saiu"],
            "itens_alterados": arq["mudou"],
        }

    corpo = montar_corpo_email_alteracoes(alterados, detalhes)
    logo_cid = make_msgid(domain="finaud.com.br")[1:-1]
    html = gerar_html_email(corpo, "22/07/2026", logo_cid)

    out = BASE / "dados" / "backups" / "preview_email_limpo_22jul.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html.replace(f"cid:{logo_cid}", "../logotipo/FINAUD_TEC_LOG.jpg"), encoding="utf-8")
    print("PREVIEW", out)

    cfg = load_email_config(CONFIG_PATH)
    to = cfg.get("to") or ["michel@finaud.com.br"]
    msg = MIMEMultipart()
    msg["Subject"] = (
        f"[SIMULAÇÃO tabela resumo] Atenção: Atualização na página de Leiautes "
        f"do Bacen na data: 22/07/2026"
    )
    msg["From"] = cfg["from"]
    msg["To"] = ", ".join(to)
    msg.attach(MIMEText(html, "html", "utf-8"))
    with open(LOGO_PATH, "rb") as f:
        img = MIMEImage(f.read())
        img.add_header("Content-ID", f"<{logo_cid}>")
        img.add_header("Content-Disposition", "inline", filename="logo.jpg")
        msg.attach(img)

    smtp_class = smtplib.SMTP_SSL if cfg["ssl"] else smtplib.SMTP
    with smtp_class(cfg["host"], cfg["port"]) as server:
        if cfg["tls"]:
            server.starttls()
        if cfg["user"] and cfg["password"]:
            server.login(cfg["user"], cfg["password"])
        server.sendmail(cfg["from"], to, msg.as_string())
    print("EMAIL_OK", ", ".join(to), f"({len(alterados)} arquivos, BLUE={BLUE_BRAND})")


if __name__ == "__main__":
    main()
