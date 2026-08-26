# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from persistencia.db import conectar, init_db


def _agora() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _parse_lista(valor: str | None) -> list[str]:
    if not valor:
        return []
    try:
        parsed = json.loads(valor)
        return parsed if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        return []


def _row_usuario(row) -> dict:
    data = dict(row)
    data["ativo"] = bool(data.get("ativo"))
    data["receber_email_alertas"] = bool(data.get("receber_email_alertas"))
    return data


_CAMPOS_USUARIO = (
    "id, email, nome, perfil_codigo, cargo, departamento, ativo, "
    "receber_email_alertas, criado_em, atualizado_em"
)


def buscar_usuario_por_email(email: str) -> Optional[dict]:
    init_db()
    with conectar() as conn:
        row = conn.execute(
            """
            SELECT id, email, nome, perfil_codigo, senha_hash, cargo,
                   departamento, ativo, receber_email_alertas,
                   criado_em, atualizado_em
            FROM usuarios
            WHERE lower(email) = lower(?)
            """,
            (email,),
        ).fetchone()
    return _row_usuario(row) if row else None


def buscar_usuario_por_id(usuario_id: int) -> Optional[dict]:
    init_db()
    with conectar() as conn:
        row = conn.execute(
            """
            SELECT id, email, nome, perfil_codigo, senha_hash, cargo,
                   departamento, ativo, receber_email_alertas,
                   criado_em, atualizado_em
            FROM usuarios
            WHERE id = ?
            """,
            (usuario_id,),
        ).fetchone()
    return _row_usuario(row) if row else None


def listar_usuarios() -> tuple[list[dict], int]:
    init_db()
    with conectar() as conn:
        total = conn.execute("SELECT COUNT(*) AS c FROM usuarios").fetchone()["c"]
        rows = conn.execute(
            f"""
            SELECT {_CAMPOS_USUARIO}
            FROM usuarios
            ORDER BY nome COLLATE NOCASE
            """
        ).fetchall()
    return [_row_usuario(row) for row in rows], int(total)


def obter_usuario(usuario_id: int) -> Optional[dict]:
    init_db()
    with conectar() as conn:
        row = conn.execute(
            f"""
            SELECT {_CAMPOS_USUARIO}
            FROM usuarios
            WHERE id = ?
            """,
            (usuario_id,),
        ).fetchone()
    return _row_usuario(row) if row else None


def _emails_unicos(rows) -> list[str]:
    vistos: set[str] = set()
    saida: list[str] = []
    for row in rows:
        email = str(row["email"] or "").strip()
        chave = email.lower()
        if not email or "@" not in email or chave in vistos:
            continue
        vistos.add(chave)
        saida.append(email)
    return saida


def listar_emails_alerta() -> list[str]:
    """E-mails de usuários ativos com flag de alerta ligado (ordem estável)."""
    init_db()
    with conectar() as conn:
        rows = conn.execute(
            """
            SELECT email
            FROM usuarios
            WHERE ativo = 1 AND receber_email_alertas = 1
            ORDER BY email COLLATE NOCASE
            """
        ).fetchall()
    return _emails_unicos(rows)


def listar_emails_administradores() -> list[str]:
    """E-mails de administradores ativos (alerta técnico; não usa a flag do comunicado)."""
    init_db()
    with conectar() as conn:
        rows = conn.execute(
            """
            SELECT email
            FROM usuarios
            WHERE ativo = 1 AND perfil_codigo = 'administrador'
            ORDER BY email COLLATE NOCASE
            """
        ).fetchall()
    return _emails_unicos(rows)


def criar_usuario(data: dict) -> int:
    init_db()
    agora = _agora()
    with conectar() as conn:
        cur = conn.execute(
            """
            INSERT INTO usuarios (
                email, nome, perfil_codigo, senha_hash, cargo, departamento,
                ativo, receber_email_alertas, criado_em, atualizado_em
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["email"],
                data["nome"],
                data.get("perfil_codigo", "operador"),
                data.get("senha_hash", ""),
                data.get("cargo"),
                data.get("departamento"),
                1 if data.get("ativo", True) else 0,
                1 if data.get("receber_email_alertas", True) else 0,
                agora,
                agora,
            ),
        )
        return int(cur.lastrowid)


def atualizar_senha_usuario(usuario_id: int, senha_hash: str) -> bool:
    init_db()
    with conectar() as conn:
        cur = conn.execute(
            """
            UPDATE usuarios
            SET senha_hash = ?, atualizado_em = ?
            WHERE id = ?
            """,
            (senha_hash, _agora(), usuario_id),
        )
        return cur.rowcount > 0


def atualizar_usuario(usuario_id: int, data: dict) -> Optional[dict]:
    atual = obter_usuario(usuario_id)
    if not atual:
        return None
    novo = {**atual, **data}
    with conectar() as conn:
        conn.execute(
            """
            UPDATE usuarios
            SET email = ?, nome = ?, perfil_codigo = ?, cargo = ?,
                departamento = ?, ativo = ?, receber_email_alertas = ?,
                atualizado_em = ?
            WHERE id = ?
            """,
            (
                novo["email"],
                novo["nome"],
                novo["perfil_codigo"],
                novo.get("cargo"),
                novo.get("departamento"),
                1 if novo.get("ativo", True) else 0,
                1 if novo.get("receber_email_alertas", False) else 0,
                _agora(),
                usuario_id,
            ),
        )
    return obter_usuario(usuario_id)


def excluir_usuario(usuario_id: int) -> bool:
    init_db()
    with conectar() as conn:
        cur = conn.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))
        return cur.rowcount > 0


def listar_permissoes_perfis() -> dict[str, list[str]]:
    init_db()
    with conectar() as conn:
        rows = conn.execute(
            "SELECT perfil_codigo, rotas_permitidas FROM perfis_permissoes ORDER BY perfil_codigo"
        ).fetchall()
    return {row["perfil_codigo"]: _parse_lista(row["rotas_permitidas"]) for row in rows}


def salvar_permissoes_perfis(permissoes: dict[str, list[str]]) -> dict[str, list[str]]:
    init_db()
    agora = _agora()
    with conectar() as conn:
        for perfil, rotas in permissoes.items():
            conn.execute(
                """
                INSERT INTO perfis_permissoes (
                    perfil_codigo, rotas_permitidas, atualizado_em
                ) VALUES (?, ?, ?)
                ON CONFLICT(perfil_codigo) DO UPDATE SET
                    rotas_permitidas = excluded.rotas_permitidas,
                    atualizado_em = excluded.atualizado_em
                """,
                (perfil, json.dumps(rotas, ensure_ascii=False), agora),
            )
    return listar_permissoes_perfis()
