# -*- coding: utf-8 -*-
"""Reenvia o e-mail de uma execução já gravada, só para LEIAUTES_EMAIL_TEST_TO."""
from __future__ import annotations

import argparse
import os
import smtplib
import sys
from email import encoders
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import make_msgid
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))
if str(BASE / "scripts") not in sys.path:
    sys.path.insert(0, str(BASE / "scripts"))

from persistencia.arquivos_db import (
    reprocessar_alteracoes_arquivo_novo,
    reprocessar_comparacoes_execucao,
)
from persistencia.db import conectar, init_db
from persistencia.execucoes_db import obter_execucao, obter_ultima_execucao
from verifica_leiautes_finaud import (
    ASSUNTO,
    CONFIG_PATH,
    LOGO_PATH,
    _carregar_detalhes_alteracoes,
    gerar_html_email,
    gerar_planilha_antes_depois,
    load_email_config,
    montar_corpo_email_alteracoes,
)


def _alterados_da_execucao(detalhes: dict) -> list[dict]:
    itens = []
    for url, det in detalhes.items():
        itens.append(
            {
                "url": url,
                "evidencia": det.get("resumo_executivo") or "",
            }
        )
    return itens


def _execucao_do_xsd_v5() -> int:
    init_db()
    with conectar() as conn:
        row = conn.execute(
            """
            SELECT a.execucao_id
            FROM alteracoes_detectadas a
            JOIN arquivos_monitorados ar ON ar.id = a.arquivo_id
            WHERE ar.nome_arquivo LIKE '%XSD v5%'
               OR ar.nome_arquivo LIKE '%v5.xsd'
            ORDER BY a.execucao_id DESC
            LIMIT 1
            """
        ).fetchone()
    return int(row["execucao_id"]) if row else 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execucao-id", type=int, default=0)
    args = parser.parse_args()
    test_to = os.environ.get("LEIAUTES_EMAIL_TEST_TO", "").strip()
    if not test_to:
        raise SystemExit(
            "Defina LEIAUTES_EMAIL_TEST_TO (um e-mail só) antes de enviar."
        )

    ultima = obter_ultima_execucao()
    execucao_id = (
        args.execucao_id
        or _execucao_do_xsd_v5()
        or (int(ultima["id"]) if ultima else 0)
    )
    if not execucao_id:
        raise SystemExit("Nenhuma execução encontrada.")

    n = reprocessar_alteracoes_arquivo_novo(execucao_id)
    n2 = reprocessar_comparacoes_execucao(execucao_id)
    print(
        f"Execução {execucao_id}: {n} arquivo(s) novo(s) com comparação; "
        f"{n2} comparação(ões) reprocessada(s)."
    )

    detalhes = _carregar_detalhes_alteracoes(execucao_id)
    alterados = _alterados_da_execucao(detalhes)
    if not alterados:
        raise SystemExit(f"Execução {execucao_id} não tem alterações para o e-mail.")

    os.environ["LEIAUTES_EMAIL_TEST_TO"] = test_to
    email_cfg = load_email_config(CONFIG_PATH)
    destinatarios = email_cfg.get("to") or []
    if not destinatarios:
        raise SystemExit("Nenhum destinatário após LEIAUTES_EMAIL_TEST_TO.")

    msg = MIMEMultipart()
    msg["Subject"] = ASSUNTO + " (conferência)"
    msg["From"] = email_cfg["from"]
    msg["To"] = ", ".join(destinatarios)

    logo_cid = make_msgid(domain="finaud.com.br")[1:-1]
    corpo = montar_corpo_email_alteracoes(alterados, detalhes, {})
    from datetime import datetime

    ex = obter_execucao(execucao_id) or {}
    inicio = str(ex.get("iniciado_em") or "")
    try:
        hoje = datetime.fromisoformat(inicio).strftime("%d/%m/%Y")
    except ValueError:
        hoje = datetime.now().strftime("%d/%m/%Y")
    corpo_html = gerar_html_email(corpo, hoje, logo_cid)
    msg.attach(MIMEText(corpo_html, "html", "utf-8"))

    with open(LOGO_PATH, "rb") as f:
        img = MIMEImage(f.read())
        img.add_header("Content-ID", f"<{logo_cid}>")
        img.add_header("Content-Disposition", "inline", filename="logo.jpg")
        msg.attach(img)

    planilha = gerar_planilha_antes_depois(alterados, detalhes)
    if planilha:
        content_xlsx, nome_xlsx = planilha
        part = MIMEBase(
            "application",
            "vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        part.set_payload(content_xlsx)
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", "attachment", filename=nome_xlsx)
        msg.attach(part)

    smtp_class = smtplib.SMTP_SSL if email_cfg["ssl"] else smtplib.SMTP
    with smtp_class(email_cfg["host"], email_cfg["port"]) as server:
        if email_cfg["tls"]:
            server.starttls()
        if email_cfg["user"] and email_cfg["password"]:
            server.login(email_cfg["user"], email_cfg["password"])
        server.sendmail(email_cfg["from"], destinatarios, msg.as_string())
    print(f"E-mail enviado para: {', '.join(destinatarios)}")


if __name__ == "__main__":
    main()
