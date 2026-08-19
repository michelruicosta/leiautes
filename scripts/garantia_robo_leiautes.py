# -*- coding: utf-8 -*-
"""
Garantia automática do robô leiautes (roda sozinha via cron).

O que faz:
  1) Scrape das páginas Bacen — nenhuma pode voltar sem anexos.
  2) Classificação e-mail — arquivo novo = precisa agir; técnico mostra "O que mudou".
  3) Diff PDF (se houver v7/v8 no storage) — coluna "O que mudou" em português.
  4) HTML do e-mail — blocos e textos esperados.

Alerta:
  - Só envia e-mail se ALGUMA checagem falhar (para michel@ / LEIAUTES_EMAIL_TEST_TO).
  - Se tudo OK, só grava log (sem spam).

Uso:
  .venv/bin/python scripts/garantia_robo_leiautes.py
"""
from __future__ import annotations

import os
import smtplib
import sys
import traceback
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))

LOG_DIR = RAIZ / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_PATH = LOG_DIR / "garantia-robo.log"


def _log(msg: str) -> None:
    linha = f"{datetime.now():%Y-%m-%d %H:%M:%S} {msg}"
    print(linha, flush=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(linha + "\n")


def _checagem(nome: str, fn, falhas: list[str]) -> None:
    try:
        fn()
        _log(f"OK  | {nome}")
    except Exception as exc:
        detalhe = f"{nome}: {exc}"
        falhas.append(detalhe)
        _log(f"FALHA | {detalhe}")
        _log(traceback.format_exc())


def check_scrape_paginas() -> None:
    import verifica_leiautes_finaud as m

    erros = []
    for url in m.urls:
        if "leiautedocumentoscrd" in url.lower():
            # 4111 tem extrator próprio; cobre no smoke mínimo via anexos > 0
            pass
        datas, anexos, _cats = m.extrair_datas_categorias_e_anexos(url)
        del datas
        if len(anexos) < 1:
            erros.append(f"{url} → 0 anexos (página Angular vazia?)")
        else:
            _log(f"     scrape {url.split('/')[-1]}: {len(anexos)} anexo(s)")
    if erros:
        raise RuntimeError("; ".join(erros))


def check_classificacao_email() -> None:
    import verifica_leiautes_finaud as m

    # Arquivo novo → precisa agir
    det_novo = {
        "resumo_executivo": "Arquivo novo observado na página do Bacen.",
        "itens_incluidos": ["Novo arquivo na página."],
        "itens_removidos": [],
        "itens_alterados": ["novo arquivo observado"],
    }
    if m._detalhe_so_tecnico(det_novo, "novo arquivo observado"):
        raise RuntimeError("arquivo novo foi classificado como técnico (deveria precisar agir)")

    # Técnico → não precisa agir + descrição
    det_tech = {
        "resumo_executivo": "Alteracao detectada por metadados: etag mudou; last_modified mudou",
        "itens_incluidos": [],
        "itens_removidos": [],
        "itens_alterados": ["etag mudou; last_modified mudou; content_length mudou"],
    }
    if not m._detalhe_so_tecnico(det_tech, "etag mudou; last_modified mudou"):
        raise RuntimeError("mudança só de metadados NÃO foi classificada como técnica")

    frase = m._descrever_mudanca_tecnica(
        "etag mudou; last_modified mudou; content_length mudou",
        det_tech,
    )
    if "data de publicação" not in frase and "tamanho" not in frase and "etag" not in frase:
        raise RuntimeError(f"descrição técnica fraca: {frase!r}")

    # HTML misto
    url_acao = "https://example.local/novo.pdf"
    url_tech = "https://example.local/tech.pdf"
    alterados = [
        {"url": url_acao, "evidencia": "novo arquivo observado"},
        {"url": url_tech, "evidencia": "etag mudou; last_modified mudou"},
    ]
    detalhes = {
        url_acao: {
            "nome_arquivo": "novo.pdf",
            "leiaute_codigo": "DLO-2061",
            "resumo_executivo": "Arquivo novo na página.",
            "itens_incluidos": ["Novo arquivo na página."],
            "itens_removidos": [],
            "itens_alterados": [
                'Página 1: mudanca "acrescentou \\"(AR1)\\""; antes "x"; depois "x (AR1)"'
            ],
        },
        url_tech: {
            "nome_arquivo": "tech.pdf",
            "leiaute_codigo": "DLO-2061",
            "resumo_executivo": "Alteracao detectada por metadados: etag mudou",
            "itens_incluidos": [],
            "itens_removidos": [],
            "itens_alterados": ["etag mudou; last_modified mudou"],
        },
    }
    html = m.montar_corpo_email_alteracoes(alterados, detalhes)
    for trecho in (
        "Precisa agir",
        "Não precisa agir",
        "O que fazer",
        "O que mudou",
        "Antes_Depois_leiautes",
        "removeu aba",
        "acrescentou aba",
    ):
        if trecho not in html:
            raise RuntimeError(f"HTML do e-mail sem trecho esperado: {trecho!r}")

    planilha = m.gerar_planilha_antes_depois(alterados, detalhes)
    if not planilha:
        raise RuntimeError("gerar_planilha_antes_depois retornou vazio")
    content_xlsx, nome_xlsx = planilha
    if "Antes_Depois_leiautes" not in nome_xlsx or not content_xlsx:
        raise RuntimeError(f"anexo Antes/Depois inválido: {nome_xlsx!r} ({len(content_xlsx)} bytes)")


def check_diff_pdf_se_disponivel() -> None:
    from backend.app.services.comparador_arquivos import comparar_arquivos

    v7s = list((RAIZ / "storage").rglob("*v7-vi8*Preench*.pdf")) + list(
        (RAIZ / "storage").rglob("*v7-vi8*Instru*.pdf")
    )
    v8s = list((RAIZ / "storage").rglob("*v8-vi9*Preench*.pdf")) + list(
        (RAIZ / "storage").rglob("*v8-vi9*Instru*.pdf")
    )
    if not v7s or not v8s:
        _log("     diff PDF pulado (sem v7/v8 no storage) — ok")
        return
    v7 = sorted(v7s, key=lambda p: p.stat().st_mtime)[-1]
    v8 = sorted(v8s, key=lambda p: p.stat().st_mtime)[-1]
    cmp = comparar_arquivos(
        caminho_anterior=str(v7),
        caminho_atual=str(v8),
        tipo_arquivo="pdf",
    )
    if not cmp:
        raise RuntimeError("comparar_arquivos retornou vazio")
    alts = cmp.get("itens_alterados") or []
    if not alts:
        # Pode acontecer se filtrar tudo como ruído; ainda assim exige formato quando houver
        _log("     diff PDF sem alterações após filtro — ok")
        return
    amostra = " ".join(alts[:5])
    if "mudanca" not in amostra and "acrescentou" not in amostra and "removeu" not in amostra:
        raise RuntimeError("diff PDF sem frase 'O que mudou' (mudanca/acrescentou/removeu)")


def check_descrever_mudanca() -> None:
    from backend.app.services.comparador_arquivos import _descrever_mudanca

    d = _descrever_mudanca("abc))))).", "abc))))). (AR1)")
    if "acrescentou" not in d or "AR1" not in d:
        raise RuntimeError(f"descrever mudanca falhou: {d!r}")


def _enviar_alerta(falhas: list[str]) -> None:
    import html as html_mod
    import verifica_leiautes_finaud as m

    cfg = m.load_email_config(m.CONFIG_PATH)
    dest = cfg.get("to") or ["michel@finaud.com.br"]
    hoje = datetime.now().strftime("%d/%m/%Y %H:%M")
    lista = "".join(f"<li>{html_mod.escape(f)}</li>" for f in falhas)
    corpo = f"""
    <html><body style="font-family:Arial,sans-serif;color:#222">
      <p><strong>Garantia do robô leiautes — FALHOU</strong> em {hoje}</p>
      <p>O check-up automático encontrou problema(s). O monitoramento das 18h
      pode estar em risco — revise antes de confiar no alerta do dia.</p>
      <ol>{lista}</ol>
      <p>Log: <code>{LOG_PATH}</code></p>
      <p style="color:#777;font-size:12px">E-mail automático — FINAUD TEC</p>
    </body></html>
    """.strip()
    msg = MIMEMultipart()
    msg["Subject"] = f"⚠️ Garantia leiautes FALHOU — {datetime.now():%d/%m/%Y}"
    msg["From"] = cfg["from"]
    msg["To"] = ", ".join(dest)
    msg.attach(MIMEText(corpo, "html", "utf-8"))
    smtp_class = smtplib.SMTP_SSL if cfg["ssl"] else smtplib.SMTP
    with smtp_class(cfg["host"], cfg["port"]) as server:
        if cfg["tls"]:
            server.starttls()
        if cfg["user"] and cfg["password"]:
            server.login(cfg["user"], cfg["password"])
        server.sendmail(cfg["from"], dest, msg.as_string())
    _log(f"Alerta de falha enviado para: {', '.join(dest)}")


def main() -> int:
    os.environ.setdefault("LEIAUTES_EMAIL_TEST_TO", "michel@finaud.com.br")
    os.environ.setdefault("LEIAUTES_DISABLE_STATUS_TAIL", "1")
    _log("=== INÍCIO garantia robô leiautes ===")
    falhas: list[str] = []
    _checagem("descrever mudança (AR1)", check_descrever_mudanca, falhas)
    _checagem("classificação + HTML do e-mail", check_classificacao_email, falhas)
    _checagem("diff PDF v7×v8 (se existir)", check_diff_pdf_se_disponivel, falhas)
    _checagem("scrape páginas Bacen (anexos > 0)", check_scrape_paginas, falhas)

    if falhas:
        _log(f"=== FIM com {len(falhas)} FALHA(S) ===")
        try:
            _enviar_alerta(falhas)
        except Exception as exc:
            _log(f"Não foi possível enviar e-mail de alerta: {exc}")
        return 1

    _log("=== FIM OK — sem e-mail (tudo certo) ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
