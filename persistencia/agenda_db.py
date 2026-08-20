# -*- coding: utf-8 -*-
"""Agenda do robô leiautes (horários/dias lidos pela tela e pelo --checar-agenda)."""
from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any, Optional

from persistencia.db import conectar, init_db


def _agora() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _parse_list(valor: Any) -> list:
    if valor is None:
        return []
    if isinstance(valor, list):
        return valor
    try:
        parsed = json.loads(valor)
        return parsed if isinstance(parsed, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def _ensure_schema() -> None:
    init_db()
    with conectar() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS config_agenda (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                horarios TEXT NOT NULL DEFAULT '["18:00"]',
                dias_semana TEXT NOT NULL DEFAULT '[0,1,2,3,4]',
                feriados TEXT NOT NULL DEFAULT '[]',
                robo_ativo INTEGER NOT NULL DEFAULT 1,
                atualizado_em TEXT NOT NULL
            )
            """
        )
        row = conn.execute("SELECT id FROM config_agenda WHERE id = 1").fetchone()
        if row is None:
            conn.execute(
                """
                INSERT INTO config_agenda (id, horarios, dias_semana, feriados, robo_ativo, atualizado_em)
                VALUES (1, ?, ?, '[]', 1, ?)
                """,
                (
                    json.dumps(["18:00"], ensure_ascii=False),
                    json.dumps([0, 1, 2, 3, 4], ensure_ascii=False),
                    _agora(),
                ),
            )


def obter_config_agenda() -> dict[str, Any]:
    _ensure_schema()
    with conectar() as conn:
        row = conn.execute("SELECT * FROM config_agenda WHERE id = 1").fetchone()
    if row is None:
        return {
            "horarios": ["18:00"],
            "dias_semana": [0, 1, 2, 3, 4],
            "feriados": [],
            "robo_ativo": True,
            "atualizado_em": None,
        }
    return {
        "horarios": _parse_list(row["horarios"]),
        "dias_semana": [int(d) for d in _parse_list(row["dias_semana"])],
        "feriados": _parse_list(row["feriados"]),
        "robo_ativo": bool(row["robo_ativo"]),
        "atualizado_em": row["atualizado_em"],
    }


def atualizar_config_agenda(
    *,
    horarios: Optional[list[str]] = None,
    dias_semana: Optional[list[int]] = None,
    feriados: Optional[list[str]] = None,
    robo_ativo: Optional[bool] = None,
) -> dict[str, Any]:
    _ensure_schema()
    atual = obter_config_agenda()

    if horarios is not None:
        limpos: list[str] = []
        for h in horarios:
            hh = str(h).strip()[:5]
            if re.match(r"^\d{2}:\d{2}$", hh):
                limpos.append(hh)
        horarios_final = limpos
    else:
        horarios_final = atual.get("horarios") or ["18:00"]

    if dias_semana is not None:
        dias_final = sorted({int(d) for d in dias_semana if 0 <= int(d) <= 6})
    else:
        dias_final = atual.get("dias_semana") or [0, 1, 2, 3, 4]

    feriados_final = (
        [str(f).strip() for f in feriados if str(f).strip()]
        if feriados is not None
        else (atual.get("feriados") or [])
    )
    ativo_final = (
        bool(robo_ativo) if robo_ativo is not None else bool(atual.get("robo_ativo", True))
    )

    with conectar() as conn:
        conn.execute(
            """
            UPDATE config_agenda SET
                horarios = ?,
                dias_semana = ?,
                feriados = ?,
                robo_ativo = ?,
                atualizado_em = ?
            WHERE id = 1
            """,
            (
                json.dumps(horarios_final, ensure_ascii=False),
                json.dumps(dias_final, ensure_ascii=False),
                json.dumps(feriados_final, ensure_ascii=False),
                1 if ativo_final else 0,
                _agora(),
            ),
        )
    return obter_config_agenda()


def deve_executar_agora(agora: Optional[datetime] = None) -> tuple[bool, str]:
    """Usado pelo cron * * * * *: retorna (pode_rodar, motivo)."""
    cfg = obter_config_agenda()
    if not cfg.get("robo_ativo", True):
        return False, "Robô desligado na agenda."

    dt = agora or datetime.now()
    hoje = dt.date().isoformat()
    if hoje in set(cfg.get("feriados") or []):
        return False, f"Feriado configurado ({hoje})."

    dias = set(cfg.get("dias_semana") or [])
    if dt.weekday() not in dias:
        return False, "Dia da semana fora da agenda."

    horarios = cfg.get("horarios") or []
    if not horarios:
        return False, "Nenhum horário configurado."

    atual = dt.strftime("%H:%M")
    for h in horarios:
        if not isinstance(h, str):
            continue
        hh = h.strip()[:5]
        if re.match(r"^\d{2}:\d{2}$", hh) and atual == hh:
            return True, f"Horário {hh}."
    return False, f"Fora dos horários ({atual})."
