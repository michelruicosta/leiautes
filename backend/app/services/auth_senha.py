# -*- coding: utf-8 -*-
from __future__ import annotations

import re

_RE_MAIUSCULA = re.compile(r"[A-Z]")
_RE_MINUSCULA = re.compile(r"[a-z]")
_RE_NUMERO = re.compile(r"\d")
_RE_ESPECIAL = re.compile(r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\;/]")


def validar_politica_senha(senha: str) -> str | None:
    if len(senha) < 8:
        return "A senha deve ter no mínimo 8 caracteres."
    if not _RE_MAIUSCULA.search(senha):
        return "A senha deve incluir pelo menos uma letra maiúscula."
    if not _RE_MINUSCULA.search(senha):
        return "A senha deve incluir pelo menos uma letra minúscula."
    if not _RE_NUMERO.search(senha):
        return "A senha deve incluir pelo menos um número."
    if not _RE_ESPECIAL.search(senha):
        return "A senha deve incluir pelo menos um caractere especial."
    return None

