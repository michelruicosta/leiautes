# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from app.config import RAIZ_PROJETO, SCRIPT_MOTOR
from persistencia.db import finalizar_execucao, iniciar_execucao


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


def status_robo() -> dict:
    return {
        "script_motor": str(SCRIPT_MOTOR),
        "script_existe": SCRIPT_MOTOR.exists(),
    }


def executar_robo_atual(
    *,
    modo_teste: bool = False,
    data_teste: str | None = None,
    timeout_segundos: int = 900,
) -> ResultadoRobo:
    if not SCRIPT_MOTOR.exists():
        raise FileNotFoundError(f"Script do motor nao encontrado: {SCRIPT_MOTOR}")

    env = os.environ.copy()
    if modo_teste:
        env["LEIAUTES_MODO_TESTE"] = "1"
    if data_teste:
        env["MONITOR_TEST_DATE"] = data_teste

    execucao_id = iniciar_execucao(log_path=None)
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
        status = "sucesso" if proc.returncode == 0 else "erro"
        finalizar_execucao(
            execucao_id,
            status=status,
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
        finalizar_execucao(
            execucao_id,
            status="erro",
            erro=f"Timeout apos {timeout_segundos}s",
        )
        return ResultadoRobo(
            execucao_id=execucao_id,
            status="erro",
            returncode=124,
            stdout_tail=_tail((exc.stdout or "") if isinstance(exc.stdout, str) else ""),
            stderr_tail=f"Timeout apos {timeout_segundos}s",
        )
    except Exception as exc:
        finalizar_execucao(execucao_id, status="erro", erro=str(exc))
        raise
