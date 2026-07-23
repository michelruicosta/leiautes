# -*- coding: utf-8 -*-
"""E-mail com dados REAIS do alerta de 22/07/2026 (robô antigo).

Fonte: log monitor_leiautes_20260722.log + manifesto atual.
Não há binários da versão anterior → sem diff de célula/texto; evidência = metadados HTTP.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import smtplib
import sys
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import make_msgid
from pathlib import Path
from urllib.parse import unquote, urlparse

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

LOG_OLD = Path(
    "/home/tsalachtech.com.br/apps/leiautes/logs/monitor_leiautes_20260722.log"
)
MANIFEST_OLD = Path(
    "/home/tsalachtech.com.br/apps/leiautes/scripts/manifest_arquivos.json"
)
MANIFEST_NEW = BASE / "scripts" / "manifest_arquivos.json"


def _nome(url: str) -> str:
    return unquote(urlparse(url).path).split("/")[-1].strip() or "arquivo"


def _parse_log(path: Path) -> list[dict]:
    pat = re.compile(
        r"Alteração detectada em anexo: (?P<url>https\S+) \| (?P<ev>.+)$"
    )
    itens = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = pat.search(line)
        if not m:
            continue
        url = m.group("url").strip()
        ev = m.group("ev").strip().rstrip(";")
        itens.append({"url": url, "evidencia": ev.replace("; ", ", ")})
    return itens


def _manifest_meta(url: str, manifests: list[dict]) -> dict:
    for man in manifests:
        if url in man:
            return man[url] or {}
        # match by filename
        nome = _nome(url)
        for u, meta in man.items():
            if _nome(u) == nome:
                return meta or {}
    return {}


def main() -> None:
    if not LOG_OLD.exists():
        raise SystemExit(f"Log não encontrado: {LOG_OLD}")

    alterados = _parse_log(LOG_OLD)
    if len(alterados) != 14:
        print(f"AVISO: esperava 14 alterações no log, achei {len(alterados)}")

    manifests = []
    for p in (MANIFEST_OLD, MANIFEST_NEW):
        if p.exists():
            manifests.append(json.loads(p.read_text(encoding="utf-8")))

    detalhes = {}
    for item in alterados:
        url = item["url"]
        meta = _manifest_meta(url, manifests)
        lm = meta.get("last_modified") or "—"
        etag = meta.get("etag") or "—"
        size = meta.get("content_length") or "—"
        # Evidência real do log + metadados atuais conhecidos (pós-mudança).
        itens_alterados = [
            f'Metadados detectados em 22/07/2026: antes "(versão anterior não arquivada)"; '
            f'depois "{item["evidencia"]}"',
            f'Last-Modified atual (pós-alerta): antes "—"; depois "{lm}"',
            f'Tamanho atual (bytes): antes "—"; depois "{size}"',
            f'ETag atual: antes "—"; depois "{etag}"',
        ]
        detalhes[url] = {
            "leiaute_codigo": "DLO-2061",
            "nome_arquivo": _nome(url),
            "tipo_arquivo": Path(_nome(url)).suffix.lstrip(".") or "arquivo",
            "resumo_executivo": (
                "Alteração real registrada pelo robô em 22/07/2026 às 18h "
                "(metadados HTTP). A versão anterior do arquivo não foi "
                "arquivada, então não há diff de célula/texto."
            ),
            "impacto_sugerido": (
                "Revisar o arquivo no Bacen e as rotinas internas que o consomem."
            ),
            "itens_incluidos": [],
            "itens_removidos": [],
            "itens_alterados": itens_alterados,
        }

    corpo = _motor.montar_corpo_email_alteracoes(alterados, detalhes)

    logo_cid = make_msgid(domain="finaud.com.br")[1:-1]
    html = _motor.gerar_html_email(corpo, "22/07/2026", logo_cid)

    out = BASE / "dados" / "backups" / "email_real_22jul_metadados.html"
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
        "[DADOS REAIS 22/07 — aviso técnico] Atualização na página de Leiautes "
        "do Bacen na data: 22/07/2026"
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
    print("EMAIL_OK", ", ".join(to), f"arquivos={len(alterados)}")


if __name__ == "__main__":
    main()
