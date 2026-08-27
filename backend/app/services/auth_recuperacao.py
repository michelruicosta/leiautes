# -*- coding: utf-8 -*-
"""Recuperação de senha — senha temporária por e-mail."""
from __future__ import annotations

import secrets
import string

from app.services.auth_email import MENSAGEM_GENERICA, enviar_senha_temporaria
from app.services.auth_senha import validar_politica_senha
from app.services.auth_sessao import hash_senha
from persistencia.auditoria_db import registrar_log
from persistencia.usuarios_db import atualizar_senha_usuario, buscar_usuario_por_email

_ESPECIAIS = "!@#$%*_-+"
_LETRAS = string.ascii_letters
_DIGITOS = string.digits


def gerar_senha_temporaria(tamanho: int = 12) -> str:
    tamanho = max(tamanho, 8)
    alfabeto = _LETRAS + _DIGITOS + _ESPECIAIS
    for _ in range(20):
        partes = [
            secrets.choice(string.ascii_uppercase),
            secrets.choice(string.ascii_lowercase),
            secrets.choice(_DIGITOS),
            secrets.choice(_ESPECIAIS),
        ]
        partes.extend(secrets.choice(alfabeto) for _ in range(tamanho - 4))
        secrets.SystemRandom().shuffle(partes)
        senha = "".join(partes)
        if validar_politica_senha(senha) is None:
            return senha
    raise RuntimeError("Não foi possível gerar senha temporária.")


def solicitar_recuperacao_senha(email: str) -> str:
    usuario = buscar_usuario_por_email(email)
    if usuario is not None and usuario.get("ativo"):
        temp = gerar_senha_temporaria()
        if enviar_senha_temporaria(usuario["email"], usuario["nome"] or usuario["email"], temp):
            atualizar_senha_usuario(usuario["id"], hash_senha(temp))
            registrar_log(
                usuario=usuario["email"],
                pagina="Login",
                acao="Recuperação de senha",
                detalhe="Senha temporária enviada por e-mail.",
            )
    return MENSAGEM_GENERICA
