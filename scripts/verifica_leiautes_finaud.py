# -*- coding: utf-8 -*-
"""
Monitor de leiautes Bacen (v3.2a)
- Logo inline por CID
- Config de e-mail em JSON (config_email.json no diretório do projeto)
- Data "hoje" dinâmica + MONITOR_TEST_DATE opcional
- Playwright com flags para ambiente compartilhado
- **NOVO**: Envia e-mail mesmo sem novidades (configurável) e deixa o texto de "Não há documentos" alinhado à esquerda e na cor azul do logotipo (#2e3192)
"""

from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email.utils import make_msgid
from email import encoders

import ssl, smtplib, os, re, json, hashlib, requests, sys, mimetypes
from urllib.parse import urlparse, unquote
from concurrent.futures import ThreadPoolExecutor, as_completed

from datetime import datetime, timedelta
from pathlib import Path
import traceback

# >>> ajuste este caminho por projeto
TAIL_PATH_BASE = "/home/tsalachtech.com.br/public_html/monitoramentos/leiautes/_status_tail.txt"
LOG_PATH_BASE  = "/home/tsalachtech.com.br/apps/leiautes/logs/execucao_{data}.log"


def _write_status_tail(proj: str,
                       header_status: str,
                       resumo: dict,
                       ultimos: list[str] | None = None,
                       extra_info: str | None = None) -> None:
    """
    Escreve um _status_tail.txt mais rico.
    - proj: "normativos" | "leiautes"
    - header_status: ex. "🟢 OK | ..." ou "🟡 AVISO | ..." ou "🔴 ERRO | ..."
    - resumo: dict com pares "Chave" -> "Valor"
    - ultimos: lista com títulos/itens recentes (máx. 3)
    - extra_info: linha adicional (opcional)
    """

    # Determina status numérico para o painel
    status_code = 0
    if "AVISO" in header_status:
        status_code = 1
    elif "ERRO" in header_status:
        status_code = 2

    now = datetime.now()
    now_fmt = now.strftime('%d/%m/%Y %H:%M:%S')
    tail_path = TAIL_PATH_BASE.format(proj=proj)
    log_path  = LOG_PATH_BASE.format(proj=proj, data=now.strftime("%Y%m%d"))

    # Monta conteúdo a ser escrito no _status_tail
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

    # Escreve com delimitadores para o painel reconhecer
    bloco = []
    bloco.append(f"===== INÍCIO {now_fmt} =====")
    bloco.extend(lines)
    bloco.append(f"===== FIM {now_fmt} =====")

    with open(tail_path, "w", encoding="utf-8") as f:
        f.write("\n".join(bloco) + "\n\n")


    

# ====== CAMINHOS/TEMPOS ======
SCRIPT_DIR = Path(__file__).resolve().parent
BASE = SCRIPT_DIR.parent
CONFIG_PATH = BASE / "config" / "config_email.json"   # <= aqui
LOGO_PATH = BASE / "logotipo" / "FINAUD_TEC_LOG.jpg"

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

# ====== AJUSTES ======
QUIET_BASELINE = False         # 1ª execução não alerta anexos
ONLY_ATUAL = True              # monitora só URLs com /Atual/
EXCLUDE_PATTERNS = ["versoes_anteriores", "anteriores", "historico"]

ATTACH_CHANGED_FILES = True
MAX_ATTACHMENTS = 8
MAX_SINGLE_ATTACH_SIZE = 4 * 1024 * 1024    # 4 MB
MAX_TOTAL_ATTACH_SIZE = 18 * 1024 * 1024    # 18 MB

# **NOVO**: controle para enviar e-mail mesmo sem novidades
SEND_EMAIL_WHEN_NO_CHANGES = True  # deixe True para sempre enviar; False para manter comportamento antigo

# ====== PÁGINAS A MONITORAR ======
urls = [
    "https://www.bcb.gov.br/estabilidadefinanceira/leiautedocumentoDDR2011",
    "https://www.bcb.gov.br/estabilidadefinanceira/leiautedocumentoDRM",
    "https://www.bcb.gov.br/estabilidadefinanceira/leiautedoc2061",
    "https://www.bcb.gov.br/estabilidadefinanceira/leiautedoc2062",
    "https://www.bcb.gov.br/estabilidadefinanceira/leiaute_drl2160",
]

# ====== DATA DE REFERÊNCIA ======
hoje = datetime.now().strftime("%d/%m/%Y")  # Produção
#hoje = "04/09/2025"  # Testes (fixo)
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

# ====== REDE/REQUESTS ======

def _session():
    sess = requests.Session()
    sess.headers.update({"User-Agent": "FINAUD-Monitor/1.0 (+https://local)"})
    try:
        from requests.adapters import HTTPAdapter
        from urllib3.util import Retry
        retry = Retry(total=3, backoff_factor=0.5,
                      status_forcelist=[429, 500, 502, 503, 504],
                      allowed_methods=["HEAD", "GET"])
        adapter = HTTPAdapter(max_retries=retry, pool_maxsize=10)
        sess.mount("https://", adapter)
        sess.mount("http://", adapter)
    except Exception as e:
        logger.debug(f"Retry adapter não configurado: {e}")
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


# ====== ANEXOS - VERIFICAÇÃO LEVE ======
ANEXO_REGEX = re.compile(r"\.(pdf|xlsx?|xsd|zip)$", re.IGNORECASE)


def verificar_anexos(urls_anexos, use_partial_fp=True):
    manifest = _load_manifest()
    alterados, sess = [], _session()
    first_run = len(manifest) == 0

    for url in urls_anexos:
        cur = manifest.get(url, {})
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

        changed = (
            (info.get("etag") and info.get("etag") != cur.get("etag")) or
            (info.get("last_modified") and info.get("last_modified") != cur.get("last_modified")) or
            (info.get("content_length") and info.get("content_length") != cur.get("content_length")) or
            (info.get("final_url") and info.get("final_url") != cur.get("final_url"))
        )

        if not (info.get("etag") or info.get("last_modified") or info.get("content_length")) and use_partial_fp:
            if "partial_fp" not in info:
                try: info["partial_fp"] = small_range_fingerprint(sess, url)
                except Exception: pass
            if info.get("partial_fp") and info.get("partial_fp") != cur.get("partial_fp"):
                changed = True

        if changed or url not in manifest:
            if not (first_run and QUIET_BASELINE):
                reasons = []
                for k in ("etag","last_modified","content_length","final_url","partial_fp"):
                    if info.get(k) and info.get(k) != cur.get(k): reasons.append(f"{k} mudou")
                if not reasons: reasons.append("novo arquivo observado")
                logger.info(f"Alteração detectada em anexo: {url} | {'; '.join(reasons)}")
                alterados.append({"url": url, "evidencia": ", ".join(reasons)})

        manifest[url] = {
            "etag": info.get("etag"),
            "last_modified": info.get("last_modified"),
            "content_length": info.get("content_length"),
            "final_url": info.get("final_url"),
            "partial_fp": info.get("partial_fp") if use_partial_fp else cur.get("partial_fp"),
            "checked_at": info.get("checked_at"),
        }

    _save_manifest(manifest)
    return alterados, manifest


# ====== PLAYWRIGHT (datas + anexos + categorias) ======

def extrair_datas_categorias_e_anexos(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        page = browser.new_page()
        page.goto(url, timeout=60000, wait_until="load")
        try: page.wait_for_selector("table", timeout=5000)
        except: pass

        # datas dd/mm/aaaa
        datas = []
        try:
            for cell in page.query_selector_all("td"):
                text = (cell.inner_text() or "").strip()
                if len(text) == 10 and text[2] == "/" and text[5] == "/":
                    datas.append(text)
        except: pass

        # links + categoria
        try:
            items = page.evaluate("""
                () => {
                  const res = [];
                  const isAsset = (h) => /\.(pdf|xlsx?|xsd|zip)$/i.test(h||"");
                  const getCat = (el) => {
                    let node = el;
                    while (node) {
                      let prev = node.previousElementSibling;
                      while (prev) {
                        if (prev.tagName === 'H3' && prev.id === 'categoria') {
                          return (prev.textContent || '').trim() || 'Sem categoria';
                        }
                        prev = prev.previousElementSibling;
                      }
                      node = node.parentElement;
                    }
                    return 'Sem categoria';
                  };
                  for (const a of Array.from(document.querySelectorAll('a[href]'))) {
                    const href = a.getAttribute('href') || '';
                    if (!isAsset(href)) continue;
                    const abs = new URL(href, document.baseURI).toString();
                    res.push({ href: abs, text: (a.textContent || '').trim(), categoria: getCat(a) });
                  }
                  return res;
                }
            """)
        except Exception:
            items = []

        browser.close()

        categoria_por_url, anexos, seen = {}, [], set()
        for it in items:
            u = it.get("href") or ""
            if not u: continue
            pl = u.lower()
            if ONLY_ATUAL and "/atual/" not in pl: continue
            if any(pat in pl for pat in EXCLUDE_PATTERNS): continue
            if u not in seen:
                seen.add(u)
                anexos.append(u)
                categoria_por_url[u] = (it.get("categoria") or "Sem categoria").strip()

        return datas, anexos, categoria_por_url


# ====== EMAIL HTML ======

BLUE_BRAND = "#2e3192"  # azul do logotipo


def gerar_html_email(conteudo_html: str, data_ref: str, logo_cid: str) -> str:
    return f"""
<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<style>
  body {{ font-family: Arial, sans-serif; margin: 20px; color:#111; }}
  .wrap {{ width: 100%; margin: 0 auto; }}
  .item p {{ margin: 0 0 8px; line-height: 1.55; font-size: 16px; }}
  a {{ color: #1a73e8; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  .rodape {{ font-size: 12px; color: #555; margin-top: 40px; text-align: center; }}
  .sec-title {{ font-size: 18px; margin-top: 18px; color: {BLUE_BRAND}; font-weight: bold; }}
</style>
</head>
<body>
  <div class="wrap">
    <div style="text-align:center; margin-bottom: 12px;">
      <img src="cid:{logo_cid}" alt="FINAUD TEC" style="max-width:220px; height:auto;">
    </div>
    <p style="font-size:18px; margin-top:24px;">
      Foram identificadas possíveis atualizações na data de <strong>{data_ref}</strong>.
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
    """Corpo do e-mail quando NÃO há documentos; mensagem alinhada à esquerda e azul."""
    return f"""
<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<style>
  body {{ font-family: Arial, sans-serif; margin: 20px; color:#111; }}
  .wrap {{ width: 100%; margin: 0 auto; }}
  .rodape {{ font-size: 12px; color: #555; margin-top: 40px; text-align: center; }}
  .msg-sem-novidade {{ text-align: left; color: {BLUE_BRAND}; font-size: 18px; margin-top: 24px; line-height:1.55; }}
</style>
</head>
<body>
  <div class="wrap">
    <div style="text-align:center; margin-bottom: 12px;">
      <img src="cid:{logo_cid}" alt="FINAUD TEC" style="max-width:220px; height:auto;">
    </div>
    <p class="msg-sem-novidade">
      <strong>Não há documentos novos ou alterados na data de {data_ref}</strong>.
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
    logger.info("Iniciando monitoração...")

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

    alterados, manifest = verificar_anexos(anexos_detectados)
    anexos_nomes = [_filename_from_url(a["url"]) for a in alterados]

    emails_enviados = 0
    destinatarios = []

    if alterados or SEND_EMAIL_WHEN_NO_CHANGES:
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
                blocos_por_categoria = {}
                for item in alterados:
                    url = item["url"]
                    nome = _filename_from_url(url)
                    categoria = categoria_por_url.get(url, "Sem categoria")
                    evidencia = item.get("evidencia", "")
                    link = f'<a href="{url}" target="_blank" style="color:{BLUE_BRAND}; text-decoration:none;">{nome}</a>'
                    linha = f"<li>{link}</li>"

                    blocos_por_categoria.setdefault(categoria, []).append(linha)

                partes = []
                partes.append(f"<p style='font-size:17px;'><strong style='color:{BLUE_BRAND};'>Arquivo(s) encontrado(s):</strong></p>")
                for cat, blocos in blocos_por_categoria.items():
                    partes.append(f"<p><strong>{cat}</strong></p><ul>{''.join(blocos)}</ul>")
                corpo = "".join(partes)
                html = gerar_html_email(corpo, hoje, logo_cid)
            else:
                html = gerar_html_sem_novidade(hoje, logo_cid)

            msg.attach(MIMEText(html, "html", "utf-8"))

            with open(LOGO_PATH, "rb") as f:
                img = MIMEImage(f.read())
                img.add_header("Content-ID", f"<{logo_cid}>")
                img.add_header("Content-Disposition", "inline", filename="logo.jpg")
                msg.attach(img)

            session = _session()
            total_size = 0
            for item in alterados:
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

# Funções auxiliares
def _plural(n: int, sing: str, plur: str | None = None) -> str:
    if n == 1:
        return f"{n} {sing}"
    return f"{n} {plur or (sing + 's')}"

def _fmt_duracao(delta: timedelta) -> str:
    s = int(delta.total_seconds())
    h, rem = divmod(s, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


if __name__ == "__main__":
    try:
        inicio_exec = datetime.now()
        result = main()
        fim_exec = datetime.now()
        duracao = _fmt_duracao(fim_exec - inicio_exec)

        links_detectados_por_data = result.get("links_detectados_por_data", [])
        alterados = result.get("alterados", [])
        urls_alterados = [a["url"] for a in alterados]
        # Verifica se os alterados não têm data correspondente
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

        # LOGS
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

        # Cabeçalho do status
        txt_leiautes = _plural(leiautes_novos, "leiaute novo", "leiautes novos")
        txt_pdfs     = _plural(pdfs_gerados,    "PDF gerado",   "PDFs gerados")
        
        aviso_tecnico = ""
        
        if leiautes_novos > 0:
            # Novidades reais (data nova na página)
            header = f"🟢 OK | {txt_leiautes}, {txt_pdfs} | em {duracao}"
            if leiautes_novos > 0:
                exemplo_nome = nome_doc_por_url(links_detectados_por_data[0])
                header += f" | ex: {exemplo_nome}"
        
        elif alterados:  # ou: elif links_com_alteracao:
            # Sem data nova, mas anexos mudaram
            header = f"🟡 AVISO | Link(s) alterado(s), sem data nova | em {duracao}"
            aviso_tecnico = "🛈 AVISO TÉCNICO: link(s) foram alterados no Bacen, mesmo sem data nova"
        
        else:
            header = f"🟢 OK | Nenhuma alteração detectada | em {duracao}"

   
        # Gera nomes legíveis dos leiautes verificados
        codigo_para_sigla = {
            "2061": "DLO",
            "2062": "DLI",
            "DRM": "DRM",  #referência correta
            "2011": "DDR",
            "2160": "DRL",
            "2060": "DRM"  #fallback para URLs que só tem "DRM"
        }
        
        paginas_formatadas = []
        for url in urls:
            encontrado = False  # inicializa como False a cada URL
            for codigo, sigla in codigo_para_sigla.items():
                if codigo in url.upper():
                    # Se o código for "DRM", forçamos a usar 2060
                    if codigo == "DRM":
                        paginas_formatadas.append("DRM - 2060")
                    else:
                        paginas_formatadas.append(f"{sigla} - {codigo}")
                    encontrado = True
                    break
                    
            if not encontrado:
                trecho = url.rsplit("/", 1)[-1].upper().replace("LEIAUTEDOCUMENTO", "").replace("LEIAUTEDOC", "")
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

    except Exception as e:
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

    except Exception as e:
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