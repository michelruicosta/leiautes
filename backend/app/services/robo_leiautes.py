# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from app.config import RAIZ_PROJETO, SCRIPT_MOTOR
from persistencia.db import definir_log_execucao, finalizar_execucao, iniciar_execucao
from persistencia.execucoes_db import contar_resultados_execucao


@dataclass
class ResultadoRobo:
    execucao_id: int
    status: str
    returncode: int
    stdout_tail: str
    stderr_tail: str


def _tail(texto: str, limite: int = 4000) -> str:
    if len(texto) <= limite:
        return texto
    return texto[-limite:]


def _preparar_log(execucao_id: int) -> Path:
    log_dir = RAIZ_PROJETO / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    caminho = log_dir / f"execucao_robo_{execucao_id}_{stamp}.log"
    definir_log_execucao(execucao_id, str(caminho.relative_to(RAIZ_PROJETO)))
    return caminho


def _gravar_log(
    caminho: Path,
    *,
    execucao_id: int,
    cmd: list[str],
    returncode: int | None,
    stdout: str,
    stderr: str,
) -> None:
    linhas = [
        f"Execução: {execucao_id}",
        f"Iniciado em: {datetime.now().isoformat(timespec='seconds')}",
        f"Comando: {' '.join(cmd)}",
        f"Return code: {returncode if returncode is not None else 'não finalizado'}",
        "",
        "STDOUT",
        stdout.strip() or "(sem saída)",
        "",
        "STDERR",
        stderr.strip() or "(sem erro)",
        "",
    ]
    caminho.write_text("\n".join(linhas), encoding="utf-8")


def status_robo() -> dict:
    return {
        "script_motor": str(SCRIPT_MOTOR),
        "script_existe": SCRIPT_MOTOR.exists(),
    }


def executar_robo_atual(
    *,
    modo_teste: bool = False,
    enviar_email: bool = False,
    data_teste: str | None = None,
    timeout_segundos: int = 900,
) -> ResultadoRobo:
    if not SCRIPT_MOTOR.exists():
        raise FileNotFoundError(f"Script do motor nao encontrado: {SCRIPT_MOTOR}")

    env = os.environ.copy()
    execucao_id = iniciar_execucao(log_path=None)
    log_path = _preparar_log(execucao_id)
    env["LEIAUTES_EXECUCAO_ID"] = str(execucao_id)
    env.setdefault("LEIAUTES_EMAIL_TEST_TO", "michel@finaud.com.br")
    env.setdefault("LEIAUTES_DISABLE_STATUS_TAIL", "1")
    if not enviar_email:
        env["LEIAUTES_DISABLE_EMAIL"] = "1"
    if modo_teste:
        env["LEIAUTES_MODO_TESTE"] = "1"
    if data_teste:
        env["MONITOR_TEST_DATE"] = data_teste
    cmd = [sys.executable, str(SCRIPT_MOTOR)]

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(RAIZ_PROJETO),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_segundos,
            check=False,
        )
        _gravar_log(
            log_path,
            execucao_id=execucao_id,
            cmd=cmd,
            returncode=proc.returncode,
            stdout=proc.stdout or "",
            stderr=proc.stderr or "",
        )
        status = "sucesso" if proc.returncode == 0 else "erro"
        contadores = contar_resultados_execucao(execucao_id)
        finalizar_execucao(
            execucao_id,
            status=status,
            qtd_leiautes=contadores["qtd_leiautes"],
            qtd_arquivos=contadores["qtd_arquivos"],
            qtd_alteracoes=contadores["qtd_alteracoes"],
            erro=None if proc.returncode == 0 else _tail(proc.stderr or proc.stdout),
        )
        return ResultadoRobo(
            execucao_id=execucao_id,
            status=status,
            returncode=proc.returncode,
            stdout_tail=_tail(proc.stdout or ""),
            stderr_tail=_tail(proc.stderr or ""),
        )
    except subprocess.TimeoutExpired as exc:
        stdout_timeout = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
        stderr_timeout = f"Timeout apos {timeout_segundos}s"
        _gravar_log(
            log_path,
            execucao_id=execucao_id,
            cmd=cmd,
            returncode=124,
            stdout=stdout_timeout,
            stderr=stderr_timeout,
        )
        finalizar_execucao(
            execucao_id,
            status="erro",
            erro=stderr_timeout,
        )
        return ResultadoRobo(
            execucao_id=execucao_id,
            status="erro",
            returncode=124,
            stdout_tail=_tail(stdout_timeout),
            stderr_tail=stderr_timeout,
        )
    except Exception as exc:
        _gravar_log(
            log_path,
            execucao_id=execucao_id,
            cmd=cmd,
            returncode=None,
            stdout="",
            stderr=str(exc),
        )
        finalizar_execucao(execucao_id, status="erro", erro=str(exc))
        raise
