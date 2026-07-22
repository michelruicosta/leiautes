# -*- coding: utf-8 -*-
"""Importa o acervo do projeto extrator_leiautes para o histórico local.

Uso:
    python scripts/importar_historico_extrator.py

O script lê `extrações/<documento>/<grupo>`, copia os arquivos para
`storage/importados/extrator_leiautes` e registra versões no banco. Arquivos
com nomes de mesma família, como `Esquema XSD_v1.xsd` e `Esquema XSD_v2.xsd`,
são tratados como versões do mesmo item para permitir comparação.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import sys
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from persistencia.arquivos_db import registrar_arquivo_observado
from persistencia.db import conectar, finalizar_execucao, iniciar_execucao


ORIGEM_PADRAO = Path(r"D:\02_Finaud\Projetos\concluidos\extrator_leiautes\extrações")
DESTINO_BASE = BASE / "storage" / "importados" / "extrator_leiautes"
EXTS = {".pdf", ".xlsx", ".xlsm", ".xls", ".xsd", ".xml", ".zip", ".txt"}


@dataclass(frozen=True)
class ArquivoFonte:
    path: Path
    documento: str
    grupo: str
    familia: str
    url: str


def _slug(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", sem_acento.strip())
    return slug.strip("._") or "item"


def _familia(stem: str) -> str:
    texto = unicodedata.normalize("NFKD", stem).encode("ascii", "ignore").decode().lower()
    texto = re.sub(r"\s*-\s*\d+\s*kb$", "", texto)
    texto = re.sub(r"\b(v|versao)\s*[_-]?\s*\d+(\.\d+)?\b", "", texto)
    texto = re.sub(r"[_-]v\d+\b", "", texto)
    texto = re.sub(r"\bvalido[^\-()]*", "", texto)
    texto = re.sub(r"\bdata[- ]base[^\-()]*", "", texto)
    texto = re.sub(r"\bde\s+\d{2}[_/-]\d{2}[_/-]\d{4}\b", "", texto)
    texto = re.sub(r"\s+", " ", texto).strip(" -_().")
    return _slug(texto or stem)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _ja_importado(url: str, sha: str) -> bool:
    with conectar() as conn:
        row = conn.execute(
            """
            SELECT 1
            FROM arquivos_monitorados ar
            JOIN versoes_arquivos v ON v.arquivo_id = ar.id
            WHERE ar.url = ? AND v.hash_conteudo = ?
            LIMIT 1
            """,
            (url, sha),
        ).fetchone()
    return row is not None


def _coletar(origem: Path) -> list[ArquivoFonte]:
    arquivos: list[ArquivoFonte] = []
    for path in origem.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in EXTS:
            continue
        rel = path.relative_to(origem)
        if len(rel.parts) < 3:
            continue
        documento = rel.parts[0]
        grupo = rel.parts[1]
        familia = _familia(path.stem)
        url = f"extrator://{_slug(documento)}/{_slug(grupo)}/{familia}{path.suffix.lower()}"
        arquivos.append(
            ArquivoFonte(
                path=path,
                documento=documento,
                grupo=grupo,
                familia=familia,
                url=url,
            )
        )
    return sorted(arquivos, key=lambda a: (a.documento, a.grupo, a.familia, a.path.name))


def _copiar(arquivo: ArquivoFonte, sha: str) -> Path:
    destino_dir = DESTINO_BASE / _slug(arquivo.documento) / _slug(arquivo.grupo) / arquivo.familia
    destino_dir.mkdir(parents=True, exist_ok=True)
    destino = destino_dir / f"{sha[:12]}_{_slug(arquivo.path.name)}"
    if not destino.exists():
        shutil.copy2(arquivo.path, destino)
    return destino


def importar(origem: Path, limite: int | None = None) -> tuple[int, int, int]:
    arquivos = _coletar(origem)
    if limite:
        arquivos = arquivos[:limite]

    execucao_id = iniciar_execucao(log_path="importacao_extrator_leiautes")
    importados = 0
    pulados = 0
    alteracoes = 0
    documentos = set()

    try:
        for arquivo in arquivos:
            sha = _sha256(arquivo.path)
            if _ja_importado(arquivo.url, sha):
                pulados += 1
                continue

            destino = _copiar(arquivo, sha)
            stat = arquivo.path.stat()
            primeira_versao = not _tem_arquivo(arquivo.url)
            _, _, alteracao_id = registrar_arquivo_observado(
                url=arquivo.url,
                nome_arquivo=arquivo.path.name,
                info={
                    "etag": sha,
                    "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
                    "content_length": str(stat.st_size),
                    "final_url": str(arquivo.path),
                    "partial_fp": sha,
                    "checked_at": datetime.now().isoformat(timespec="seconds"),
                    "origem": "extrator_leiautes",
                },
                categoria=f"{arquivo.documento} - {arquivo.grupo}",
                execucao_id=None if primeira_versao else execucao_id,
                mudou=True,
                evidencia="importação do histórico extrator_leiautes",
                caminho_arquivo=str(destino),
            )
            importados += 1
            documentos.add(arquivo.documento)
            if alteracao_id is not None:
                alteracoes += 1

        finalizar_execucao(
            execucao_id,
            status="sucesso",
            qtd_leiautes=len(documentos),
            qtd_arquivos=importados,
            qtd_alteracoes=alteracoes,
        )
    except Exception as exc:
        finalizar_execucao(
            execucao_id,
            status="erro",
            qtd_leiautes=len(documentos),
            qtd_arquivos=importados,
            qtd_alteracoes=alteracoes,
            erro=str(exc),
        )
        raise
    return importados, pulados, alteracoes


def _tem_arquivo(url: str) -> bool:
    with conectar() as conn:
        row = conn.execute(
            "SELECT 1 FROM arquivos_monitorados WHERE url = ? LIMIT 1",
            (url,),
        ).fetchone()
    return row is not None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--origem", type=Path, default=ORIGEM_PADRAO)
    parser.add_argument("--limite", type=int, default=None)
    args = parser.parse_args()
    importados, pulados, alteracoes = importar(args.origem, args.limite)
    print(
        f"Importação concluída: {importados} arquivo(s), "
        f"{pulados} já existiam, {alteracoes} alteração(ões)."
    )


if __name__ == "__main__":
    main()
