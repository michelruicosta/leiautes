# -*- coding: utf-8 -*-
"""
Monitor de leiautes Bacen (v3.2a+4111)
- Logo inline por CID
- Config de e-mail em JSON (config_email.json no diretório do projeto)
- Data "hoje" dinâmica + MONITOR_TEST_DATE opcional
- Playwright com flags para ambiente compartilhado
- **NOVO**: Envia e-mail mesmo sem novidades (configurável) e deixa o texto de "Não há documentos" alinhado à esquerda e na cor azul do logotipo (#2e3192)
- **NOVO**: Suporte ao Documento 4111 (Saldos Contábeis Diários - SCD)
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from playwright.sync_api import sync_playwright
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email.utils import make_msgid
from email import encoders

import html, ssl, smtplib, os, re, json, hashlib, requests, sys, mimetypes, traceback
from urllib.parse import urlparse, unquote

# >>> ajuste este caminho por projeto
TAIL_PATH_BASE = "/home/tsalachtech.com.br/public_html/monitoramentos/leiautes/_status_tail.txt"
LOG_PATH_BASE  = "/home/tsalachtech.com.br/apps/leiautes/logs/execucao_{data}.log"


def _write_status_tail(proj: str,
                       header_status: str,
                       resumo: dict,
                       ultimos: list[str] | None = None,
                       extra_info: str | None = None) -> None:
    if os.environ.get("LEIAUTES_DISABLE_STATUS_TAIL", "").strip().lower() in (
        "1",
        "true",
        "yes",
    ):
        logger.info("Status tail legado desativado por LEIAUTES_DISABLE_STATUS_TAIL=1.")
        return

    status_code = 0
    if "AVISO" in header_status:
        status_code = 1
    elif "ERRO" in header_status:
        status_code = 2

    now = datetime.now()
    now_fmt = now.strftime('%d/%m/%Y %H:%M:%S')
    tail_path = TAIL_PATH_BASE.format(proj=proj)
    log_path  = LOG_PATH_BASE.format(proj=proj, data=now.strftime("%Y%m%d"))

    lines = []
    lines.append(f"{now_fmt} | {header_status}")
    if extra_info:
        lines.append(extra_info)

    lines.append("")
    lines.append("📊 Resumo:")
    for k, v in resumo.items():
        lines.append(f"- {k}: {v}")

    if ultimos:
        lines.append("")
        lines.append("📜 Últimos itens lidos:")
        for t in ultimos[:3]:
            lines.append(f"- {t[:120]}")

    lines.append("")
    lines.append(f"ℹ️ Log completo: {log_path}")

    bloco = []
    bloco.append(f"===== INÍCIO {now_fmt} =====")
    bloco.extend(lines)
    bloco.append(f"===== FIM {now_fmt} =====")

    with open(tail_path, "w", encoding="utf-8") as f:
        f.write("\n".join(bloco) + "\n\n")


# ====== CAMINHOS/TEMPOS ======
SCRIPT_DIR = Path(__file__).resolve().parent
BASE = SCRIPT_DIR.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))
CONFIG_PATH = BASE / "config" / "config_email.json"
LOGO_PATH = BASE / "logotipo" / "FINAUD_TEC_LOG.jpg"

try:
    from persistencia.arquivos_db import (
        registrar_arquivo_observado,
        salvar_conteudo_versao,
    )
    from persistencia.db import (
        conectar,
        finalizar_execucao,
        init_db,
        iniciar_execucao,
    )
    from persistencia.execucoes_db import contar_resultados_execucao
except Exception:
    registrar_arquivo_observado = None
    salvar_conteudo_versao = None
    conectar = None
    init_db = None
    iniciar_execucao = None
    finalizar_execucao = None
    contar_resultados_execucao = None

CONNECT_TIMEOUT = 10
READ_TIMEOUT = 10
TIMEOUT = (CONNECT_TIMEOUT, READ_TIMEOUT)

# ====== LOGGING ======
import logging
from logging.handlers import RotatingFileHandler

LOG_DIR = BASE / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"monitor_leiautes_{datetime.now():%Y%m%d}.log"

logger = logging.getLogger("monitor_leiautes")
logger.setLevel(logging.INFO)
if not logger.handlers:
    fh = RotatingFileHandler(LOG_FILE, maxBytes=1_000_000, backupCount=7, encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(fh)
    logger.addHandler(sh)

# ====== AJUSTES (fallback; preferir configuracoes do banco) ======
QUIET_BASELINE = True
ONLY_ATUAL = True
EXCLUDE_PATTERNS = ["versoes_anteriores", "anteriores", "historico", "manual_cadip"]

ATTACH_CHANGED_FILES = True
MAX_ATTACHMENTS = 8
MAX_SINGLE_ATTACH_SIZE = 4 * 1024 * 1024
MAX_TOTAL_ATTACH_SIZE = 18 * 1024 * 1024

SEND_EMAIL_WHEN_NO_CHANGES = True


def _as_bool(valor, default: bool = False) -> bool:
    if isinstance(valor, bool):
        return valor
    if valor is None:
        return default
    return str(valor).strip().lower() in {"1", "true", "yes", "sim", "on"}


def _carregar_flags_monitor() -> tuple[bool, bool]:
    """Lê monitor.quiet_baseline / monitor.only_atual da tela (tabela configuracoes)."""
    quiet = QUIET_BASELINE
    only_atual = ONLY_ATUAL
    try:
        from persistencia.config_db import obter_configuracao

        quiet = _as_bool(obter_configuracao("monitor.quiet_baseline", quiet), quiet)
        only_atual = _as_bool(obter_configuracao("monitor.only_atual", only_atual), only_atual)
    except Exception as e:
        logger.warning(f"Config do monitor indisponível; usando defaults. Motivo: {e}")
    return quiet, only_atual


def _metadados_mudaram(info: dict, anterior: dict, use_partial_fp: bool = True) -> tuple[bool, list[str]]:
    """Compara Last-Modified/etag/etc. com a baseline anterior. Sem anterior = sem mudança real."""
    if not anterior:
        return False, []
    reasons: list[str] = []
    for key in ("etag", "last_modified", "content_length", "final_url"):
        atual = info.get(key)
        if atual and atual != anterior.get(key):
            reasons.append(f"{key} mudou")
    if use_partial_fp:
        atual_fp = info.get("partial_fp")
        if atual_fp and atual_fp != anterior.get("partial_fp"):
            reasons.append("partial_fp mudou")
    return bool(reasons), reasons

# ====== PÁGINAS A MONITORAR ======
urls = [
    "https://www.bcb.gov.br/estabilidadefinanceira/leiautedocumentoDDR2011",
    "https://www.bcb.gov.br/estabilidadefinanceira/leiautedocumentoDRM",
    "https://www.bcb.gov.br/estabilidadefinanceira/leiautedoc2061",
    "https://www.bcb.gov.br/estabilidadefinanceira/leiautedoc2062",
    "https://www.bcb.gov.br/estabilidadefinanceira/leiaute_drl2160",
    "https://www.bcb.gov.br/estabilidadefinanceira/leiautedocumentoscrd",  # 4111 - SCD
]

# ====== DATA DE REFERÊNCIA ======
hoje = datetime.now().strftime("%d/%m/%Y")
ASSUNTO = f"📢 Atenção: Atualização na página de Leiautes do Bacen na data: {hoje}"

# ====== MANIFEST ======
MANIFEST_PATH = SCRIPT_DIR / "manifest_arquivos.json"

def _load_manifest():
    if MANIFEST_PATH.exists():
        try:
            return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning(f"Falha ao ler manifest: {e}")
    return {}

def _save_manifest(data):
    MANIFEST_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

# ====== REDE ======
def _session():
    sess = requests.Session()
    sess.headers.update({"User-Agent": "FINAUD-Monitor/1.0 (+https://local)"})
    return sess

def head_info(session, url):
    r = session.head(url, allow_redirects=True, timeout=TIMEOUT)
    r.raise_for_status()
    return {
        "etag": r.headers.get("ETag"),
        "last_modified": r.headers.get("Last-Modified"),
        "content_length": r.headers.get("Content-Length"),
        "final_url": r.url,
        "status": r.status_code,
        "checked_at": datetime.now().isoformat(),
    }

def small_range_fingerprint(session, url, length=1024):
    headers = {"Range": f"bytes=0-{length-1}"}
    r = session.get(url, headers=headers, stream=True, allow_redirects=True, timeout=TIMEOUT)
    if r.status_code not in (200, 206): r.raise_for_status()
    chunk = next(r.iter_content(length), b"")
    return hashlib.sha256(chunk).hexdigest()


def baixar_conteudo_para_historico(session, url, max_single=MAX_SINGLE_ATTACH_SIZE):
    try:
        hi = head_info(session, url)
        cl = hi.get("content_length")
        if cl and cl.isdigit() and int(cl) > max_single:
            return None, f"pula historico: Content-Length {cl} > limite"
    except Exception:
        pass

    r = session.get(url, stream=True, allow_redirects=True, timeout=TIMEOUT)
    if r.status_code != 200:
        return None, f"status {r.status_code}"

    data, total = bytearray(), 0
    for chunk in r.iter_content(64 * 1024):
        if not chunk:
            break
        data.extend(chunk)
        total += len(chunk)
        if total > max_single:
            return None, f"pula historico: excedeu {max_single} bytes"
    return bytes(data), None

# ====== ANEXOS ======
ANEXO_REGEX = re.compile(r"\.(pdf|xlsx?|xsd|zip)$", re.IGNORECASE)

def verificar_anexos(urls_anexos, categoria_por_url=None, execucao_id=None, use_partial_fp=True):
    """Compara anexos com a baseline anterior.

    Regra (item 3):
    - primeira observação de um URL: grava manifesto/baseline, sem evidência "Mudou";
    - evidência só quando Last-Modified/etag/hash mudou em relação à baseline.
    """
    quiet_baseline, _only_atual = _carregar_flags_monitor()
    manifest = _load_manifest()
    alterados, sess = [], _session()
    first_run = len(manifest) == 0
    categoria_por_url = categoria_por_url or {}
    primeiras_obs = 0

    if first_run:
        logger.info(
            "Manifesto vazio: primeira baseline. quiet_baseline=%s "
            "(evidências só em mudanças reais de metadados).",
            quiet_baseline,
        )

    for url in urls_anexos:
        cur = manifest.get(url, {})
        eh_primeira_obs = url not in manifest
        try:
            info = head_info(sess, url)
        except Exception as e:
            if use_partial_fp:
                try:
                    fp = small_range_fingerprint(sess, url)
                    info = {"etag":None,"last_modified":None,"content_length":None,
                            "final_url":url,"partial_fp":fp,"status":None,
                            "checked_at": datetime.now().isoformat()}
                except Exception as e2:
                    logger.warning(f"HEAD/Range falhou para {url}: {e2}")
                    manifest[url] = {**cur,"error": f"HEAD/Range fail: {e2}","checked_at": datetime.now().isoformat()}
                    continue
            else:
                logger.warning(f"HEAD falhou para {url}: {e}")
                manifest[url] = {**cur,"error": f"HEAD fail: {e}","checked_at": datetime.now().isoformat()}
                continue

        if not (info.get("etag") or info.get("last_modified") or info.get("content_length")) and use_partial_fp:
            if "partial_fp" not in info:
                try:
                    info["partial_fp"] = small_range_fingerprint(sess, url)
                except Exception:
                    pass

        mudanca_real, reasons = _metadados_mudaram(
            info, cur if not eh_primeira_obs else {}, use_partial_fp
        )
        evidencia = ""
        if mudanca_real:
            logger.info(f"Alteração detectada em anexo: {url} | {', '.join(reasons)}")
            evidencia = ", ".join(reasons)
            alterados.append({"url": url, "evidencia": evidencia})
        elif eh_primeira_obs:
            primeiras_obs += 1
            logger.info(f"Baseline silenciosa (primeira observação): {url}")

        # Versão de conteúdo: mudança real, ou primeira obs (baseline sem evidência).
        precisa_versao = mudanca_real or eh_primeira_obs
        caminho_arquivo = None
        if salvar_conteudo_versao and precisa_versao:
            try:
                conteudo, motivo_historico = baixar_conteudo_para_historico(sess, url)
                if conteudo:
                    caminho_arquivo = salvar_conteudo_versao(
                        conteudo=conteudo,
                        nome_arquivo=_filename_from_url(url),
                        categoria=categoria_por_url.get(url),
                    )
                    logger.info(f"Versão salva para histórico: {caminho_arquivo}")
                elif motivo_historico:
                    logger.warning(f"Não foi possível salvar histórico de {url} | Motivo: {motivo_historico}")
            except Exception as e:
                logger.warning(f"Falha ao salvar versão no histórico: {url} | {e}")

        if registrar_arquivo_observado:
            try:
                registrar_arquivo_observado(
                    url=url,
                    nome_arquivo=_filename_from_url(url),
                    info=info,
                    categoria=categoria_por_url.get(url),
                    execucao_id=execucao_id,
                    mudou=precisa_versao,
                    evidencia=evidencia,
                    caminho_arquivo=caminho_arquivo,
                    gerar_evidencia=mudanca_real,
                )
            except Exception as e:
                logger.warning(f"Falha ao registrar arquivo no banco: {url} | {e}")

        manifest[url] = {
            "etag": info.get("etag"),
            "last_modified": info.get("last_modified"),
            "content_length": info.get("content_length"),
            "final_url": info.get("final_url"),
            "partial_fp": info.get("partial_fp") if use_partial_fp else cur.get("partial_fp"),
            "checked_at": info.get("checked_at"),
        }

    _save_manifest(manifest)
    if primeiras_obs:
        logger.info(
            "Primeiras observações sem evidência: %s arquivo(s). Mudanças reais: %s.",
            primeiras_obs,
            len(alterados),
        )
    return alterados, manifest, {
        "first_run": first_run,
        "quiet_baseline": quiet_baseline,
        "primeiras_observacoes": primeiras_obs,
    }


# ====== PLAYWRIGHT ======
def extrair_anexos_4111(page):
    linha_4111 = page.locator("tr").filter(has_text="4111")
    urls_4111, categorias = [], {}
    if linha_4111.count() > 0:
        links = linha_4111.locator("a")
        for i in range(links.count()):
            href = links.nth(i).get_attribute("href")
            if href:
                abs_url = page.evaluate("url => new URL(url, document.baseURI).toString()", href)
                if any(s in abs_url.lower() for s in [".pdf", ".xsd"]):
                    urls_4111.append(abs_url)
                    categorias[abs_url] = "4111 - SCD"
    return urls_4111, categorias


def _categoria_da_pagina(page_url: str) -> str:
    u = (page_url or "").lower()
    if "leiautedocumentoscrd" in u or "scrd" in u:
        return "4111 - SCD"
    if "ddr2011" in u or "documentoDDR".lower() in u:
        return "DDR-2011"
    if "leiautedocumentodrm" in u or "drm" in u:
        return "DRM-2060"
    if "leiautedoc2061" in u or "2061" in u:
        return "DLO-2061"
    if "leiautedoc2062" in u or "2062" in u:
        return "DLI-2062"
    if "drl2160" in u or "2160" in u:
        return "DRL-2160"
    return "Sem categoria"


def _filtrar_urls_anexos(candidatos: list[str]) -> list[str]:
    """Aplica excludes e only_atual.

    Páginas DLO/DLI usam pasta /Atual/. DRM/DRL não usam — nesses casos
    only_atual vira 'excluir histórico' (versoes_anteriores etc.), não exige /atual/.
    """
    limpos = []
    for u in candidatos:
        pl = (u or "").lower()
        if not pl:
            continue
        if any(pat in pl for pat in EXCLUDE_PATTERNS):
            continue
        limpos.append(u)

    if not ONLY_ATUAL:
        return limpos

    com_atual = [u for u in limpos if "/atual/" in u.lower()]
    if com_atual:
        return com_atual
    return limpos


def extrair_datas_categorias_e_anexos(url):
    categoria_pagina = _categoria_da_pagina(url)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        page = browser.new_page()
        # DRM/DRL são Angular: precisa esperar a hidratação dos links.
        wait_mode = "networkidle" if any(x in url.lower() for x in ("drm", "drl2160")) else "load"
        page.goto(url, timeout=90000, wait_until=wait_mode)
        try:
            page.wait_for_selector("a[href]", timeout=8000)
        except Exception:
            pass
        if wait_mode == "networkidle":
            page.wait_for_timeout(3000)

        if "leiautedocumentoscrd" in url.lower():
            anexos_4111, categorias_4111 = extrair_anexos_4111(page)
            browser.close()
            return [], anexos_4111, categorias_4111

        datas = []
        try:
            for cell in page.query_selector_all("td"):
                text = (cell.inner_text() or "").strip()
                if len(text) == 10 and text[2] == "/" and text[5] == "/":
                    datas.append(text)
        except Exception:
            pass

        hrefs: list[str] = []
        try:
            hrefs.extend(
                page.evaluate(
                    r"""() => {
                      const res = [];
                      const isAsset = (h) => /\.(pdf|xlsx?|xsd|zip)$/i.test(h||"");
                      for (const a of Array.from(document.querySelectorAll('a[href]'))) {
                        const href = a.getAttribute('href') || '';
                        if (!isAsset(href)) continue;
                        res.push(new URL(href, document.baseURI).toString());
                      }
                      return res;
                    }"""
                )
            )
        except Exception:
            pass

        # Complemento: assets embutidos no HTML (ex.: XSD do DRM que às vezes não vira <a>).
        try:
            html = page.content()
            for m in re.findall(
                r"https?://[^\"'\s<>]+?\.(?:pdf|xlsx?|xsd|zip)",
                html,
                flags=re.I,
            ):
                hrefs.append(m)
            for m in re.findall(
                r"[\"']((?:/)?content/[^\"']+\.(?:pdf|xlsx?|xsd|zip))[\"']",
                html,
                flags=re.I,
            ):
                hrefs.append(page.evaluate("u => new URL(u, document.baseURI).toString()", m))
        except Exception:
            pass

        browser.close()

        anexos = _filtrar_urls_anexos(list(dict.fromkeys(hrefs)))
        categoria_por_url = {u: categoria_pagina for u in anexos}
        return datas, anexos, categoria_por_url


# ====== EMAIL HTML ======
BLUE_BRAND = "#2e3192"


def _parse_json_lista(valor):
    if not valor:
        return []
    try:
        parsed = json.loads(valor)
        return parsed if isinstance(parsed, list) else []
    except Exception:
        return []


def _carregar_detalhes_alteracoes(execucao_id):
    if not execucao_id or not conectar or not init_db:
        return {}
    try:
        init_db()
        with conectar() as conn:
            rows = conn.execute(
                """
                SELECT
                    ar.url,
                    ar.nome_arquivo,
                    ar.tipo_arquivo,
                    COALESCE(l.codigo, '') AS leiaute_codigo,
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
                """,
                (execucao_id,),
            ).fetchall()
    except Exception as exc:
        logger.warning(f"Nao foi possivel carregar detalhes das alteracoes: {exc}")
        return {}

    detalhes = {}
    for row in rows:
        data = dict(row)
        data["itens_incluidos"] = _parse_json_lista(data.get("itens_incluidos"))
        data["itens_removidos"] = _parse_json_lista(data.get("itens_removidos"))
        data["itens_alterados"] = _parse_json_lista(data.get("itens_alterados"))
        detalhes[data["url"]] = data
    return detalhes


def _parse_evidencia_item(texto: str) -> dict:
    padroes = [
        r'^(.*?): antes "([\s\S]*)"; depois "([\s\S]*)"$',
        r"^(.*?): antes '([\s\S]*)'; depois '([\s\S]*)'$",
        r"^(.*?): (linha anterior.*?); antes \((.*)\); depois \((.*)\)$",
        # XLSX/XLS do comparador: "Aba X, célula A1: antes valor; depois valor"
        r"^(.*?): antes ([\s\S]*); depois ([\s\S]*)$",
    ]
    for padrao in padroes:
        m = re.match(padrao, texto)
        if not m:
            continue
        if len(m.groups()) == 4:
            return {"local": f"{m.group(1)} - {m.group(2)}", "antes": m.group(3), "depois": m.group(4)}
        return {"local": m.group(1), "antes": m.group(2), "depois": m.group(3)}

    m = re.match(r'^(.*?): incluído "([\s\S]*)"$', texto)
    if m:
        return {"local": m.group(1), "depois": m.group(2)}
    m = re.match(r'^(.*?): removido "([\s\S]*)"$', texto)
    if m:
        return {"local": m.group(1), "antes": m.group(2)}
    m = re.match(r'^Arquivo interno incluído: ([^;]+); evidência: "([\s\S]*)"$', texto)
    if m:
        return {"local": f"Arquivo interno {m.group(1)}", "depois": m.group(2)}
    return {"local": "Evidência", "depois": texto}


def _grupo_local(local: str) -> str:
    m = re.match(r"^(Página \d+)", local)
    if m:
        return m.group(1)
    m = re.match(r"^(Arquivo interno [^-:]+)", local)
    if m:
        return m.group(1).strip()
    if re.match(r"^linha (atual|anterior) \d+", local, flags=re.I):
        return "Linhas do arquivo"
    return local


def _numeros_linha(itens: list[dict], removido: bool = False) -> str:
    padrao = r"linha anterior (\d+)" if removido else r"linha atual (\d+)"
    numeros = []
    for item in itens:
        m = re.search(padrao, item.get("local", ""), flags=re.I)
        if m:
            numeros.append(int(m.group(1)))
    if not numeros:
        return ""
    numeros.sort()
    if len(numeros) == 1:
        return f"linha {numeros[0]}"
    return f"linhas {numeros[0]} a {numeros[-1]}"


def _inicia_paragrafo(linha: str) -> bool:
    return bool(
        re.match(r"^\d{2}/\d{2}/\d{4}", linha)
        or re.match(r"^Item\s+\d", linha, flags=re.I)
        or re.match(r"^[-•]", linha)
        or re.match(r"^Instrução Normativa", linha, flags=re.I)
        or re.match(r"^Resolução", linha, flags=re.I)
    )


def _limpar_texto_evidencia(texto: str) -> str:
    texto = re.sub(r"\s+", " ", str(texto)).strip()
    texto = re.sub(r"([^\W\d_])[-‐‑–]\s+([^\W\d_])", r"\1\2", texto, flags=re.UNICODE)
    texto = re.sub(r"\s+([,.;:])", r"\1", texto)
    return texto


def _consolidar_textos(textos: list[str]) -> tuple[list[str], int]:
    paragrafos = []
    atual = ""
    extras = 0

    def flush():
        nonlocal atual
        if atual.strip():
            paragrafos.append(_limpar_texto_evidencia(atual))
        atual = ""

    for bruto in textos:
        linha = _limpar_texto_evidencia(str(bruto))
        if not linha:
            continue
        mais = re.match(r"^\.\.\. mais (\d+)", linha, flags=re.I)
        if mais:
            extras += int(mais.group(1))
            continue
        if _inicia_paragrafo(linha):
            flush()
            atual = linha
        elif atual and (not re.search(r"[.!?:;)]$", atual) or re.match(r"^[a-záéíóúàâêôãõç]", linha)):
            atual = f"{atual} {linha}"
        else:
            flush()
            atual = linha
    flush()
    return paragrafos, extras


def _html_card_simples(titulo: str, textos: list[str], removido: bool = False) -> str:
    paragrafos, extras = _consolidar_textos(textos)
    corpo = "".join(f"<p>{html.escape(p)}</p>" for p in paragrafos)
    if extras:
        corpo += f"<p class='more'>+ {extras} trecho(s) adicional(is) no arquivo.</p>"
    return f"""
      <div class="evidence-card">
        <div class="evidence-head"><strong>{html.escape(titulo)}</strong></div>
        <div class="evidence-body">{corpo}</div>
      </div>
    """


# Limite de linhas de evidência por arquivo no e-mail (leitura limpa).
MAX_DIFFS_EMAIL = 5


def _contagem_curta(detalhe: dict | None, evidencia: str = "") -> str:
    if not detalhe:
        return evidencia or "metadados alterados"
    n_in = len(detalhe.get("itens_incluidos") or [])
    n_out = len(detalhe.get("itens_removidos") or [])
    n_ch = len(detalhe.get("itens_alterados") or [])
    partes = []
    if n_ch:
        partes.append(f"{n_ch} mudou")
    if n_in:
        partes.append(f"{n_in} entrou")
    if n_out:
        partes.append(f"{n_out} saiu")
    if not partes:
        return evidencia or "alteração detectada"
    return " · ".join(partes)


def _html_tabela_mudancas(itens: list[str]) -> str:
    """Uma tabela compacta Local | Antes | Depois (sem cards aninhados)."""
    if not itens:
        return ""
    linhas = []
    for texto in itens[:MAX_DIFFS_EMAIL]:
        item = _parse_evidencia_item(str(texto))
        local = html.escape(str(item.get("local") or "Alteração"))
        antes = html.escape(str(item.get("antes") or "—"))
        depois = html.escape(str(item.get("depois") or "—"))
        linhas.append(
            f"<tr><td class='col-local'>{local}</td>"
            f"<td>{antes}</td><td>{depois}</td></tr>"
        )
    extra = ""
    if len(itens) > MAX_DIFFS_EMAIL:
        extra = (
            f"<p class='more'>+ {len(itens) - MAX_DIFFS_EMAIL} "
            f"alteração(ões) adicional(is) — consulte o arquivo anexo ou o Bacen.</p>"
        )
    return f"""
      <table class="diff-table" role="presentation" cellpadding="0" cellspacing="0">
        <thead>
          <tr>
            <th>Onde</th><th>Antes</th><th>Depois</th>
          </tr>
        </thead>
        <tbody>
          {''.join(linhas)}
        </tbody>
      </table>
      {extra}
    """


def _html_lista_simples(titulo: str, tipo: str, itens: list[str]) -> str:
    """Lista curta para inclusões/remoções — omitida se vazia."""
    if not itens:
        return ""
    bullets = []
    for texto in itens[:MAX_DIFFS_EMAIL]:
        item = _parse_evidencia_item(str(texto))
        if tipo == "saiu":
            trecho = item.get("antes") or item.get("depois") or texto
        else:
            trecho = item.get("depois") or item.get("antes") or texto
        local = item.get("local") or "Item"
        bullets.append(
            f"<li><strong>{html.escape(str(local))}:</strong> "
            f"{html.escape(str(trecho))}</li>"
        )
    extra = ""
    if len(itens) > MAX_DIFFS_EMAIL:
        extra = f"<p class='more'>+ {len(itens) - MAX_DIFFS_EMAIL} item(ns) adicional(is).</p>"
    return f"""
      <p class="sec-label">{html.escape(titulo)}</p>
      <ul class="compact-list">{''.join(bullets)}</ul>
      {extra}
    """


def _html_lista_diferencas(titulo: str, tipo: str, itens: list[str], vazio: str = "") -> str:
    """Compat: seções vazias não aparecem (e-mail limpo)."""
    del vazio  # não mostrar estado vazio
    if not itens:
        return ""
    if tipo == "mudou":
        return f'<p class="sec-label">{html.escape(titulo)}</p>{_html_tabela_mudancas(itens)}'
    return _html_lista_simples(titulo, tipo, itens)


def _html_detalhe_alteracao(item, detalhe) -> str:
    url = item["url"]
    nome = _filename_from_url(url)
    evidencia = item.get("evidencia") or ""
    link = (
        f'<a href="{html.escape(url)}" target="_blank" '
        f'style="color:{BLUE_BRAND}; text-decoration:none;">{html.escape(nome)}</a>'
    )
    if not detalhe:
        ev = f" — <span class='muted'>{html.escape(evidencia)}</span>" if evidencia else ""
        return f"<div class='file-block'><p class='file-title'>{link}{ev}</p></div>"

    codigo = (detalhe.get("leiaute_codigo") or "").strip()
    titulo_nome = detalhe.get("nome_arquivo") or nome
    titulo = html.escape(f"{codigo} · {titulo_nome}" if codigo else str(titulo_nome))
    contagem = html.escape(_contagem_curta(detalhe, evidencia))

    incluidos = detalhe.get("itens_incluidos") or []
    alterados = detalhe.get("itens_alterados") or []
    removidos = detalhe.get("itens_removidos") or []
    secoes = "".join(
        [
            _html_lista_diferencas("Entrou", "entrou", incluidos),
            _html_lista_diferencas("Mudou", "mudou", alterados),
            _html_lista_diferencas("Saiu", "saiu", removidos),
        ]
    )
    if not secoes and evidencia:
        secoes = f"<p class='muted'>{html.escape(evidencia)}</p>"

    return f"""
      <div class="file-block">
        <p class="file-title">{titulo}</p>
        <p class="file-meta">{link} · {contagem}</p>
        {secoes}
      </div>
    """


def montar_corpo_email_alteracoes(
    alterados: list[dict],
    detalhes_por_url: dict,
    categoria_por_url: dict | None = None,
) -> str:
    """Corpo limpo: resumo em tabela + detalhes só com mudanças reais."""
    del categoria_por_url  # agrupamento por categoria poluía; lista única
    n = len(alterados)
    resumo_linhas = []
    detalhes_html = []
    for item in alterados:
        url = item["url"]
        nome = _filename_from_url(url)
        detalhe = detalhes_por_url.get(url) or {}
        codigo = (detalhe.get("leiaute_codigo") or "").strip() or "—"
        contagem = _contagem_curta(detalhe, item.get("evidencia") or "")
        link = (
            f'<a href="{html.escape(url)}" target="_blank">'
            f"{html.escape(nome)}</a>"
        )
        resumo_linhas.append(
            "<tr>"
            f"<td class='col-leiaute'>{html.escape(codigo)}</td>"
            f"<td>{link}</td>"
            f"<td class='col-resumo'>{html.escape(contagem)}</td>"
            "</tr>"
        )
        detalhes_html.append(_html_detalhe_alteracao(item, detalhe or None))

    return f"""
      <p class="lead-count">
        <strong style="color:{BLUE_BRAND};">{n} arquivo(s) alterado(s)</strong>
      </p>
      <table class="summary-table" role="presentation" cellpadding="0" cellspacing="0">
        <thead>
          <tr>
            <th>Leiaute</th>
            <th>Arquivo</th>
            <th>Resumo</th>
          </tr>
        </thead>
        <tbody>
          {''.join(resumo_linhas)}
        </tbody>
      </table>
      <p class="sec-title">O que mudou</p>
      {''.join(detalhes_html)}
    """


def gerar_html_email(conteudo_html: str, data_ref: str, logo_cid: str) -> str:
    return f"""
<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<style>
  body {{ font-family: Arial, sans-serif; margin: 20px; color:#111; background:#fff; }}
  .wrap {{ width: 100%; max-width: 920px; margin: 0 auto; }}
  .lead-count {{ font-size: 17px; margin: 8px 0 12px; }}
  .summary-table {{ width: 100%; border-collapse: collapse; font-size: 13px; margin: 0 0 18px; }}
  .summary-table th {{ text-align: left; background: #f5f7fa; color: #5b6b84; font-size: 12px; text-transform: uppercase; padding: 8px 9px; border: 1px solid #e7ebf0; }}
  .summary-table td {{ vertical-align: top; padding: 8px 9px; border: 1px solid #e7ebf0; line-height: 1.4; word-break: break-word; }}
  .summary-table .col-leiaute {{ width: 12%; white-space: nowrap; font-weight: bold; color: #333; }}
  .summary-table .col-resumo {{ width: 22%; white-space: nowrap; color: #333; }}
  .sec-title {{ font-size: 17px; margin: 22px 0 10px; color: {BLUE_BRAND}; font-weight: bold; border-bottom: 1px solid #e7ebf0; padding-bottom: 6px; }}
  .file-block {{ margin: 0 0 18px; padding: 0 0 14px; border-bottom: 1px solid #eef1f4; }}
  .file-block:last-child {{ border-bottom: none; }}
  .file-title {{ font-size: 16px; font-weight: bold; margin: 0 0 4px; }}
  .file-meta {{ margin: 0 0 10px; font-size: 14px; color: #333; }}
  .sec-label {{ color: {BLUE_BRAND}; font-weight: bold; font-size: 14px; margin: 10px 0 6px; }}
  .diff-table {{ width: 100%; border-collapse: collapse; font-size: 13px; margin: 0 0 8px; }}
  .diff-table th {{ text-align: left; background: #f5f7fa; color: #5b6b84; font-size: 12px; text-transform: uppercase; padding: 7px 8px; border: 1px solid #e7ebf0; }}
  .diff-table td {{ vertical-align: top; padding: 7px 8px; border: 1px solid #e7ebf0; line-height: 1.4; word-break: break-word; }}
  .diff-table .col-local {{ width: 28%; color: #333; font-weight: bold; }}
  .compact-list {{ margin: 0 0 8px 18px; padding: 0; font-size: 13px; line-height: 1.45; }}
  .compact-list li {{ margin: 0 0 4px; }}
  .more {{ color: {BLUE_BRAND}; font-size: 12px; font-weight: bold; margin: 4px 0 0; }}
  .muted {{ color: #5b6b84; font-size: 13px; }}
  a {{ color: {BLUE_BRAND}; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  .rodape {{ font-size: 12px; color: #555; margin-top: 36px; text-align: center; }}
</style>
</head>
<body>
  <div class="wrap">
    <div style="text-align:center; margin-bottom: 12px;">
      <img src="cid:{logo_cid}" alt="FINAUD TEC" style="max-width:220px; height:auto;">
    </div>
    <p style="font-size:17px; margin-top:20px; line-height:1.5;">
      Atualizações nos leiautes do Bacen em <strong>{data_ref}</strong>.
    </p>
    {conteudo_html}
    <div class="rodape">
      Este e-mail foi gerado automaticamente pelo sistema de monitoramento <b>FINAUD TEC SOLUÇÕES EM TECNOLOGIA</b>.
    </div>
  </div>
</body>
</html>
""".strip()

def gerar_html_sem_novidade(data_ref: str, logo_cid: str) -> str:
    return f"""
<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<style>
  body {{ font-family: Arial, sans-serif; margin: 20px; color:#111; }}
  .wrap {{ width: 100%; margin: 0 auto; }}
  .rodape {{ font-size: 12px; color: #555; margin-top: 40px; text-align: center; }}
  .msg-sem-novidade {{ text-align: center; color: {BLUE_BRAND}; font-size: 18px; margin-top: 24px; line-height:1.55; }}
</style>
</head>
<body>
  <div class="wrap">
    <div style="text-align:center; margin-bottom: 12px;">
      <img src="cid:{logo_cid}" alt="FINAUD TEC" style="max-width:220px; height:auto;">
    </div>
    <p class="msg-sem-novidade">
      <strong>Nenhum documento novo ou alterado foi identificado na página de leiautes em {data_ref}</strong>.
    </p>
    <div class="rodape">
      Este e-mail foi gerado automaticamente pelo sistema de monitoramento <b>FINAUD TEC SOLUÇÕES EM TECNOLOGIA</b>.
    </div>
  </div>
</body>
</html>
""".strip()


# ====== NOMES ======
def _filename_from_url(url):
    base = unquote(urlparse(url).path).split("/")[-1].strip() or "arquivo"
    return base

def nome_doc_por_url(url):
    if "DDR" in url: return "DDR (2011)"
    if "DRM" in url: return "DRM"
    if "2061" in url: return "DOC 2061"
    if "2062" in url: return "DOC 2062"
    if "2160" in url: return "DRL 2160"
    if "4111" in url: return "4111 - SCD"
    return "Desconhecido"


# ====== DOWNLOAD P/ ANEXO ======
def baixar_para_anexo(session, url, max_single=MAX_SINGLE_ATTACH_SIZE):
    try:
        hi = head_info(session, url)
        cl = hi.get("content_length")
        if cl and cl.isdigit() and int(cl) > max_single:
            return None, None, None, f"pula: Content-Length {cl} > limite"
    except Exception:
        pass

    r = session.get(url, stream=True, allow_redirects=True, timeout=TIMEOUT)
    if r.status_code != 200:
        return None, None, None, f"status {r.status_code}"

    data, total = bytearray(), 0
    for chunk in r.iter_content(64 * 1024):
        if not chunk: break
        data.extend(chunk); total += len(chunk)
        if total > max_single:
            return None, None, None, f"pula: excedeu {max_single} bytes"
    content = bytes(data)

    filename = _filename_from_url(r.url or url)
    ctype, _ = mimetypes.guess_type(filename)
    if not ctype: ctype = "application/octet-stream"
    maintype, subtype = ctype.split("/", 1)
    return content, maintype, subtype, None


# ====== CONFIG DE E-MAIL ======
def load_email_config(path: Path):
    cfg = json.loads(path.read_text(encoding="utf-8"))
    to = cfg.get("to") or cfg.get("destinatarios") or []
    if isinstance(to, str):
        to = [x.strip() for x in to.split(",") if x.strip()]
    test_to = os.environ.get("LEIAUTES_EMAIL_TEST_TO", "").strip()
    if test_to:
        to = [x.strip() for x in re.split(r"[,;]", test_to) if x.strip()]
    smtp = cfg.get("smtp", {})
    return {
        "from": cfg.get("from") or cfg.get("user"),
        "to": to,
        "user": cfg.get("user") or smtp.get("user"),
        "password": cfg.get("password") or cfg.get("senha_app") or cfg.get("pass"),
        "host": smtp.get("host", "smtp.gmail.com"),
        "port": int(smtp.get("port", 465)),
        "ssl": bool(smtp.get("ssl", True)),
        "tls": bool(smtp.get("tls", False)),
    }


# ===== DEFINIÇÃO DA MAIN =====
def main():
    global ONLY_ATUAL
    logger.info("Iniciando monitoração...")
    execucao_id_env = os.environ.get("LEIAUTES_EXECUCAO_ID", "").strip()
    execucao_id = int(execucao_id_env) if execucao_id_env.isdigit() else None
    disable_email = os.environ.get("LEIAUTES_DISABLE_EMAIL", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )
    quiet_cfg, ONLY_ATUAL = _carregar_flags_monitor()
    logger.info(
        "Flags monitor: quiet_baseline=%s only_atual=%s disable_email=%s",
        quiet_cfg,
        ONLY_ATUAL,
        disable_email,
    )

    anexos_detectados = []
    categoria_por_url = {}
    links_detectados_por_data = []

    for url in urls:
        try:
            datas, anexos, categorias = extrair_datas_categorias_e_anexos(url)
            if hoje in datas:
                links_detectados_por_data.append(url)
            for link in anexos:
                anexos_detectados.append(link)
                categoria_por_url[link] = categorias.get(link, "Sem categoria")
        except Exception as e:
            logger.warning(f"Erro ao processar URL {url}: {e}")
            continue

    alterados, manifest, flags_anexos = verificar_anexos(
        anexos_detectados,
        categoria_por_url=categoria_por_url,
        execucao_id=execucao_id,
    )
    anexos_nomes = [_filename_from_url(a["url"]) for a in alterados]
    quiet_baseline = bool(flags_anexos.get("quiet_baseline"))
    first_run = bool(flags_anexos.get("first_run"))

    emails_enviados = 0
    destinatarios = []

    if disable_email:
        logger.info("Envio de e-mail desativado por LEIAUTES_DISABLE_EMAIL=1.")
    elif first_run and quiet_baseline and not alterados:
        logger.info(
            "Primeira baseline quieta (monitor.quiet_baseline=true): e-mail omitido."
        )
    elif alterados or SEND_EMAIL_WHEN_NO_CHANGES:
        email_cfg = load_email_config(CONFIG_PATH)
        destinatarios = email_cfg.get("to", [])
        if not destinatarios:
            logger.warning("Nenhum destinatário definido para envio.")
        else:
            msg = MIMEMultipart()
            msg["Subject"] = ASSUNTO
            msg["From"] = email_cfg["from"]
            msg["To"] = ", ".join(destinatarios)

            logo_cid = make_msgid(domain="finaud.com.br")[1:-1]

            if alterados:
                detalhes_por_url = _carregar_detalhes_alteracoes(execucao_id)
                corpo = montar_corpo_email_alteracoes(
                    alterados,
                    detalhes_por_url,
                    categoria_por_url,
                )
                corpo_html = gerar_html_email(corpo, hoje, logo_cid)
            else:
                corpo_html = gerar_html_sem_novidade(hoje, logo_cid)

            msg.attach(MIMEText(corpo_html, "html", "utf-8"))

            with open(LOGO_PATH, "rb") as f:
                img = MIMEImage(f.read())
                img.add_header("Content-ID", f"<{logo_cid}>")
                img.add_header("Content-Disposition", "inline", filename="logo.jpg")
                msg.attach(img)

            # Com muitos arquivos, anexos deixam o e-mail pesado; prioriza links no corpo.
            max_anexos = 3 if len(alterados) > 3 else len(alterados)
            session = _session()
            total_size = 0
            anexados = 0
            for item in alterados:
                if anexados >= max_anexos:
                    logger.info(
                        "Anexos limitados a %s arquivo(s) para manter o e-mail leve.",
                        max_anexos,
                    )
                    break
                url = item["url"]
                content, maintype, subtype, motivo = baixar_para_anexo(session, url)
                if content:
                    if total_size + len(content) > MAX_TOTAL_ATTACH_SIZE:
                        logger.warning(f"Anexo ignorado (limite total): {_filename_from_url(url)}")
                        continue
                    part = MIMEBase(maintype, subtype)
                    part.set_payload(content)
                    encoders.encode_base64(part)
                    part.add_header("Content-Disposition", "attachment", filename=_filename_from_url(url))
                    msg.attach(part)
                    total_size += len(content)
                    anexados += 1
                elif motivo:
                    logger.warning(f"Não foi possível anexar {url} | Motivo: {motivo}")

            try:
                smtp_class = smtplib.SMTP_SSL if email_cfg["ssl"] else smtplib.SMTP
                with smtp_class(email_cfg["host"], email_cfg["port"]) as server:
                    if email_cfg["tls"]:
                        server.starttls()
                    if email_cfg["user"] and email_cfg["password"]:
                        server.login(email_cfg["user"], email_cfg["password"])
                    server.sendmail(email_cfg["from"], destinatarios, msg.as_string())
                logger.info(f"E-mail enviado para: {', '.join(destinatarios)}")
                emails_enviados = 1
            except Exception as e:
                logger.error(f"Erro ao enviar e-mail: {e}")

    return {
        "links_detectados_por_data": links_detectados_por_data,
        "alterados": alterados,
        "emails_enviados": emails_enviados,
        "destinatarios": destinatarios,
        "anexos_nomes": anexos_nomes,
    }


# ===== Helpers =====
def _plural(n: int, sing: str, plur: str | None = None) -> str:
    if n == 1:
        return f"{n} {sing}"
    return f"{n} {plur or (sing + 's')}"

def _fmt_duracao(delta: timedelta) -> str:
    s = int(delta.total_seconds())
    h, rem = divmod(s, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


# ===== MAIN RUN =====
if __name__ == "__main__":
    # Cron/CLI: cria execução no banco se a API não passou LEIAUTES_EXECUCAO_ID.
    # Sem isso, versões/alterações (antes/depois) não são gravadas e o e-mail fica só com metadados.
    execucao_propria = False
    execucao_id_cli = None
    env_exec = os.environ.get("LEIAUTES_EXECUCAO_ID", "").strip()
    if not env_exec.isdigit() and iniciar_execucao:
        try:
            execucao_id_cli = iniciar_execucao()
            os.environ["LEIAUTES_EXECUCAO_ID"] = str(execucao_id_cli)
            execucao_propria = True
            logger.info(
                "Execução %s criada pelo motor (cron/CLI) para evidências antes/depois.",
                execucao_id_cli,
            )
        except Exception as exc:
            logger.warning("Não foi possível criar execução no banco: %s", exc)

    try:
        inicio_exec = datetime.now()
        result = main()
        fim_exec = datetime.now()
        duracao = _fmt_duracao(fim_exec - inicio_exec)

        links_detectados_por_data = result.get("links_detectados_por_data", [])
        alterados = result.get("alterados", [])
        urls_alterados = [a["url"] for a in alterados]
        links_com_alteracao = not any(
            any(link.startswith(url_base) for url_base in links_detectados_por_data)
            for link in urls_alterados
        )
        emails_enviados = int(result.get("emails_enviados", 0))
        destinatarios = result.get("destinatarios", [])
        anexos_nomes = result.get("anexos_nomes", [])
        destinatarios_str = ", ".join(destinatarios) if destinatarios else "—"

        paginas_verificadas = len(urls)
        leiautes_novos = len(links_detectados_por_data)
        pdfs_gerados = len(alterados)

        logger.info(f"Total de links únicos detectados: {leiautes_novos}")
        logger.info(f"Documentos alterados: {pdfs_gerados}")
        logger.info(f"PDFs gerados: {len(anexos_nomes)}")
        if anexos_nomes:
            logger.info("Documentos gerados:")
            for nome in anexos_nomes:
                logger.info(f" - {nome}")
        else:
            logger.info("Nenhum PDF foi gerado.")

        logger.info(f"E-mails enviados: {emails_enviados}")
        logger.info(f"Destinatários: {destinatarios_str}")

        txt_leiautes = _plural(leiautes_novos, "leiaute novo", "leiautes novos")
        txt_pdfs     = _plural(pdfs_gerados,    "PDF gerado",   "PDFs gerados")
        
        aviso_tecnico = ""
        
        if leiautes_novos > 0:
            header = f"🟢 OK | {txt_leiautes}, {txt_pdfs} | em {duracao}"
            if leiautes_novos > 0:
                exemplo_nome = nome_doc_por_url(links_detectados_por_data[0])
                header += f" | ex: {exemplo_nome}"
        elif alterados:
            header = f"🟡 AVISO | Link(s) alterado(s), sem data nova | em {duracao}"
            aviso_tecnico = "🛈 AVISO TÉCNICO: link(s) foram alterados no Bacen, mesmo sem data nova"
        else:
            header = f"🟢 OK | Nenhuma alteração detectada | em {duracao}"

        # Gera nomes legíveis dos leiautes verificados
        codigo_para_sigla = {
            "2061": "DLO",
            "2062": "DLI",
            "DRM": "DRM",
            "2011": "DDR",
            "2160": "DRL",
            "2060": "DRM",
            "4111": "SCD",
        
        }
        
        paginas_formatadas = []
        for url in urls:
            encontrado = False
            for codigo, sigla in codigo_para_sigla.items():
                if codigo in url.upper():
                    if sigla == "SCD":
                        paginas_formatadas.append(f"{sigla} - 4111")
                    if codigo == "DRM":
                        paginas_formatadas.append("DRM - 2060")
                    else:
                        paginas_formatadas.append(f"{sigla} - {codigo}")
                    encontrado = True
                    break
            if not encontrado:
                trecho = url.rsplit("/", 1)[-1].upper().replace("LEIAUTEDOCUMENTO", "").replace("LEIAUTEDOC", "")
                if "SCRD" in trecho:  # <- correção
                    paginas_formatadas.append("SCD - 4111")
                else:
                    paginas_formatadas.append(f"{trecho} - (desconhecido)")        
        
        if len(paginas_formatadas) > 1:
            leiautes_str = ", ".join(paginas_formatadas[:-1]) + " e " + paginas_formatadas[-1]
        else:
            leiautes_str = paginas_formatadas[0]
        
        resumo = {
            "📄 Leiautes verificados": leiautes_str,
            "📊 Leiautes novos": leiautes_novos,
            "📄 PDFs gerados": pdfs_gerados,
            "📧 E-mails enviados": emails_enviados,
            "✉️ Destinatários": destinatarios_str,
            "📄 Arquivos com mudanças detectadas": "\n- " + "\n- ".join(anexos_nomes) if anexos_nomes else "Nenhum",
        }

        _write_status_tail("leiautes", header, resumo, [], aviso_tecnico)

        if execucao_propria and execucao_id_cli and finalizar_execucao:
            contadores = (
                contar_resultados_execucao(execucao_id_cli)
                if contar_resultados_execucao
                else {"qtd_leiautes": 0, "qtd_arquivos": 0, "qtd_alteracoes": len(alterados)}
            )
            finalizar_execucao(
                execucao_id_cli,
                status="sucesso",
                qtd_leiautes=contadores.get("qtd_leiautes", 0),
                qtd_arquivos=contadores.get("qtd_arquivos", 0),
                qtd_alteracoes=contadores.get("qtd_alteracoes", len(alterados)),
                emails_enviados=emails_enviados,
            )

    except Exception as e:
        if execucao_propria and execucao_id_cli and finalizar_execucao:
            try:
                finalizar_execucao(
                    execucao_id_cli,
                    status="erro",
                    erro=str(e).splitlines()[-1][:2000],
                )
            except Exception:
                pass
        try:
            resumo_err = {"Motivo": str(e).splitlines()[-1]}
        except Exception:
            resumo_err = {"Motivo": str(e)}
        try:
            extra = "Veja o log para o traceback completo."
            _write_status_tail("leiautes", "🔴 ERRO | Falha na execução", resumo_err, [], extra)
        except Exception as log_error:
            print("Falha ao escrever no status_tail:", log_error)
        raise
    finally:
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | === FIM leiautes ===")
