# -*- coding: utf-8 -*-
"""Envio de e-mail — recuperação de senha (molde Auditoria/Normativos)."""
from __future__ import annotations

import html
import json
import logging
import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from app import config

logger = logging.getLogger(__name__)

MENSAGEM_GENERICA = (
    "Se este e-mail estiver cadastrado e ativo, enviaremos uma senha temporária em instantes.\n\n"
    "Não recebeu? Verifique o spam ou contate o administrador do sistema."
)

_BG_HEADER = "#3333A8"
_BG_HEADER_GRAD = "#1e1e72"
_TXT_HEADER = "#ffffff"
_TXT_MUTED = "#8899bb"
_BG_BODY = "#f1f5f9"
_BG_CARD = "#ffffff"
_TXT_BODY = "#3333A8"
_TXT_SECONDARY = "#1e1e72"
_BORDER_SOFT = "#c8c8e8"
_VERDE = "#8DC63F"


def _credenciais_smtp() -> dict:
    usuario = senha = host = None
    porta = 465
    usar_ssl = True
    json_path = Path(config.RAIZ_PROJETO) / "config" / "config_email.json"
    if json_path.is_file():
        try:
            cfg = json.loads(json_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            cfg = {}
        smtp = cfg.get("smtp") or {}
        usuario = cfg.get("user") or smtp.get("user") or cfg.get("from")
        senha = cfg.get("password") or cfg.get("senha_app") or cfg.get("pass")
        host = smtp.get("host")
        try:
            porta = int(smtp.get("port") or 465)
        except (TypeError, ValueError):
            porta = 465
        if "ssl" in smtp:
            usar_ssl = bool(smtp.get("ssl"))
        elif porta == 587:
            usar_ssl = False
    usuario = (
        (usuario or os.environ.get("EMAIL_USER") or os.environ.get("EMAIL_USUARIO") or "")
        .strip()
        or None
    )
    senha = (
        (senha or os.environ.get("EMAIL_PASS") or os.environ.get("EMAIL_SENHA") or "")
        .strip()
        or None
    )
    host = (
        (host or os.environ.get("SMTP_HOST") or os.environ.get("SMTP_SERVIDOR") or "smtp.gmail.com")
        .strip()
        or "smtp.gmail.com"
    )
    porta_env = os.environ.get("SMTP_PORTA") or os.environ.get("SMTP_PORT")
    if porta_env and not json_path.is_file():
        try:
            porta = int(porta_env)
        except ValueError:
            porta = 465
        usar_ssl = porta == 465
    return {
        "usuario": usuario,
        "senha": senha,
        "host": host,
        "porta": porta,
        "ssl": usar_ssl,
    }


def smtp_configurado() -> bool:
    cred = _credenciais_smtp()
    return bool(cred["usuario"] and cred["senha"] and cred["host"] and cred["porta"])


def montar_html_senha_temporaria(
    nome: str,
    email_login: str,
    senha_temporaria: str,
    url_login: str | None = None,
) -> str:
    nome_seg = html.escape(nome.strip() or email_login)
    email_seg = html.escape(email_login.strip())
    senha_seg = html.escape(senha_temporaria)
    login_url = (url_login or config.URL_LOGIN_RECUPERACAO).rstrip("/")
    login_url_seg = html.escape(login_url)

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"><title>Leiautes Bacen — senha temporária</title></head>
<body style="margin:0;padding:24px;background:{_BG_BODY};font-family:Segoe UI,Arial,sans-serif;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
    <tr><td align="center">
      <table role="presentation" width="600" cellspacing="0" cellpadding="0"
             style="max-width:600px;background:{_BG_CARD};border-radius:12px;overflow:hidden;
                    border:1px solid {_BORDER_SOFT};">
        <tr><td style="background:linear-gradient(135deg,{_BG_HEADER},{_BG_HEADER_GRAD});
                       padding:24px 28px;color:{_TXT_HEADER};">
          <div style="font-size:12px;font-weight:700;letter-spacing:1px;color:{_VERDE};">
            FINAUD TEC
          </div>
          <div style="font-size:20px;font-weight:700;margin-top:8px;">Recuperação de acesso</div>
          <div style="font-size:13px;opacity:.9;margin-top:4px;">Leiautes Bacen · Monitoramento</div>
        </td></tr>
        <tr><td style="padding:24px 28px;color:{_TXT_BODY};font-size:14px;line-height:1.6;">
          <p>Olá, <b>{nome_seg}</b>,</p>
          <p>Use os dados abaixo para entrar:</p>
          <p><b>E-mail:</b> {email_seg}<br>
          <b>Senha temporária:</b>
          <span style="font-family:monospace;font-size:15px;">{senha_seg}</span></p>
          <p><a href="{login_url_seg}" style="color:{_BG_HEADER};font-weight:700;">Abrir o Leiautes Bacen</a></p>
          <p style="font-size:13px;color:{_TXT_SECONDARY};">
            Troque esta senha em <b>Alterar senha</b> depois de entrar.
          </p>
        </td></tr>
        <tr><td style="padding:16px 28px 24px;border-top:1px solid {_BORDER_SOFT};
                       font-size:11px;color:{_TXT_MUTED};">
          E-mail automático do sistema <b>Leiautes Bacen</b>.
          Se você não pediu, ignore esta mensagem.
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def enviar_senha_temporaria(
    destino: str,
    nome: str,
    senha_temporaria: str,
) -> bool:
    cred = _credenciais_smtp()
    usuario = cred["usuario"]
    senha_smtp = cred["senha"]
    host = cred["host"]
    porta = cred["porta"]
    if not all([usuario, senha_smtp, host, porta, destino.strip()]):
        logger.warning("auth_email: SMTP não configurado ou destino vazio")
        return False

    msg = MIMEMultipart()
    msg["From"] = usuario
    msg["To"] = destino.strip()
    msg["Subject"] = "Leiautes Bacen — senha temporária"
    msg.attach(
        MIMEText(
            montar_html_senha_temporaria(
                nome=nome,
                email_login=destino.strip(),
                senha_temporaria=senha_temporaria,
            ),
            "html",
        )
    )

    try:
        if cred["ssl"] or porta == 465:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(host, porta, context=context, timeout=30) as server:
                server.login(usuario, senha_smtp)
                server.send_message(msg)
        else:
            with smtplib.SMTP(host, porta, timeout=30) as server:
                server.starttls()
                server.login(usuario, senha_smtp)
                server.send_message(msg)
        logger.info("auth_email: senha temporária enviada")
        return True
    except Exception:
        logger.exception("auth_email: falha ao enviar senha temporária")
        return False
