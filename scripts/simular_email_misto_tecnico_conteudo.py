# -*- coding: utf-8 -*-
"""Simula e-mail misto: alterações técnicas + alterações reais de conteúdo."""
from __future__ import annotations

import importlib.util
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

_spec = importlib.util.spec_from_file_location(
    "verifica_leiautes_finaud",
    BASE / "scripts" / "verifica_leiautes_finaud.py",
)
_motor = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_motor)

# Mixto: 3 técnicos + 3 com conteúdo interno (ilustrativos).
ARQUIVOS = [
    {
        "nome": "2061-202607-v7-vi8 - Instruções de Preenchimento.pdf",
        "codigo": "DLO-2061",
        "tipo": "pdf",
        "url": "https://www.bcb.gov.br/content/estabilidadefinanceira/Leiautes2061/Atual/informacoes_tecnicas/2061-202607-v7-vi8%20-%20Instru%C3%A7%C3%B5es%20de%20Preenchimento.pdf",
        "evidencia": "etag mudou, last_modified mudou, content_length mudou",
        "modo": "tecnico",
    },
    {
        "nome": "DRM_leiaute_v4.xlsx",
        "codigo": "DRM-2060",
        "tipo": "xlsx",
        "url": "https://www.bcb.gov.br/content/estabilidadefinanceira/drm2060/informacoes_tecnicas/DRM_leiaute_v4.xlsx",
        "evidencia": "last_modified mudou",
        "modo": "tecnico",
    },
    {
        "nome": "DRL_2160_leiaute_v202607.xlsx",
        "codigo": "DRL-2160",
        "tipo": "xlsx",
        "url": "https://www.bcb.gov.br/content/estabilidadefinanceira/drl2160/DRL_2160_M1/DRL_2160_leiaute_v202607.xlsx",
        "evidencia": "etag mudou, content_length mudou",
        "modo": "tecnico",
    },
    {
        "nome": "2061-202607-v1-vi1-Leiaute do DLO.xlsx",
        "codigo": "DLO-2061",
        "tipo": "xlsx",
        "url": "https://www.bcb.gov.br/content/estabilidadefinanceira/Leiautes2061/Atual/informacoes_tecnicas/2061-202607-v1-vi1-Leiaute%20do%20DLO.xlsx",
        "evidencia": "etag mudou, last_modified mudou",
        "modo": "conteudo",
        "mudou": [
            'Aba Leiaute, célula B12, coluna Domínio: antes "1;2"; depois "1;2;3"',
            'Aba Leiaute, célula C18, coluna Descrição: antes "Saldo contábil"; depois "Saldo contábil diário"',
        ],
        "entrou": ['Aba Dominios: incluído "3 - Novo domínio"'],
        "saiu": [],
    },
    {
        "nome": "2062-202607-v2-vi3-Leiaute do DLi.xlsx",
        "codigo": "DLI-2062",
        "tipo": "xlsx",
        "url": "https://www.bcb.gov.br/content/estabilidadefinanceira/Leiautes2062/Atual/informacoes_tecnicas/2062-202607-v2-vi3-Leiaute%20do%20DLi.xlsx",
        "evidencia": "etag mudou",
        "modo": "conteudo",
        "mudou": [
            'Aba Leiaute, célula D9: antes "N"; depois "S"',
            'Aba Leiaute, célula E22: antes "10"; depois "12"',
        ],
        "entrou": [],
        "saiu": ['Aba Legado: removido "coluna auxiliar X"'],
    },
    {
        "nome": "2011-202407-v7-vi7-Instruções de Preenchimento.pdf",
        "codigo": "DDR-2011",
        "tipo": "pdf",
        "url": "https://www.bcb.gov.br/content/estabilidadefinanceira/Leiautes2011/Atual/informacoes_tecnicas/2011-202407-v7-vi7-Instru%C3%A7%C3%B5es%20de%20Preenchimento.pdf",
        "evidencia": "last_modified mudou",
        "modo": "conteudo",
        "mudou": [
            'Página 3, linha atual 12: antes "prazo de envio D+2"; depois "prazo de envio D+1"',
            'Página 5, linha atual 4: antes "versão vi6"; depois "versão vi7"',
        ],
        "entrou": [],
        "saiu": [],
    },
]


def main() -> None:
    alterados = []
    detalhes = {}
    for arq in ARQUIVOS:
        url = arq["url"]
        alterados.append({"url": url, "evidencia": arq["evidencia"]})
        if arq["modo"] == "tecnico":
            detalhes[url] = {
                "leiaute_codigo": arq["codigo"],
                "nome_arquivo": arq["nome"],
                "tipo_arquivo": arq["tipo"],
                "resumo_executivo": (
                    f"Alteracao detectada por metadados: {arq['evidencia']}"
                ),
                "impacto_sugerido": "Revisar o arquivo alterado e avaliar impacto operacional.",
                "itens_incluidos": [],
                "itens_removidos": [],
                "itens_alterados": [arq["evidencia"]],
            }
        else:
            n_in = len(arq.get("entrou") or [])
            n_out = len(arq.get("saiu") or [])
            n_ch = len(arq.get("mudou") or [])
            detalhes[url] = {
                "leiaute_codigo": arq["codigo"],
                "nome_arquivo": arq["nome"],
                "tipo_arquivo": arq["tipo"],
                "resumo_executivo": (
                    f"Foram identificadas {n_in} inclusão(ões), "
                    f"{n_out} remoção(ões) e {n_ch} alteração(ões)."
                ),
                "impacto_sugerido": (
                    "Revisar abas e células alteradas antes de atualizar rotinas internas."
                ),
                "itens_incluidos": arq.get("entrou") or [],
                "itens_removidos": arq.get("saiu") or [],
                "itens_alterados": arq.get("mudou") or [],
            }

    corpo = _motor.montar_corpo_email_alteracoes(alterados, detalhes)
    logo_cid = make_msgid(domain="finaud.com.br")[1:-1]
    html = _motor.gerar_html_email(corpo, "23/07/2026", logo_cid)

    out = BASE / "dados" / "backups" / "preview_email_misto_tecnico_conteudo.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        html.replace(f"cid:{logo_cid}", "../logotipo/FINAUD_TEC_LOG.jpg"),
        encoding="utf-8",
    )
    print("PREVIEW", out)

    cfg = _motor.load_email_config(_motor.CONFIG_PATH)
    to = cfg.get("to") or ["michel@finaud.com.br"]
    msg = MIMEMultipart()
    msg["Subject"] = (
        "[SIMULAÇÃO layout limpo] Atualização na página de Leiautes "
        "do Bacen na data: 23/07/2026"
    )
    msg["From"] = cfg["from"]
    msg["To"] = ", ".join(to)
    msg.attach(MIMEText(html, "html", "utf-8"))
    with open(_motor.LOGO_PATH, "rb") as f:
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
    print(
        "EMAIL_OK",
        ", ".join(to),
        "tecnicos=3 conteudo=3 total=",
        len(alterados),
    )


if __name__ == "__main__":
    main()
