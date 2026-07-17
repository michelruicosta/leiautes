# -*- coding: utf-8 -*-
from __future__ import annotations

import bcrypt
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.config import AUTH_SECRET_KEY, AUTH_SESSAO_MAX_AGE_SEG

_serializer = URLSafeTimedSerializer(AUTH_SECRET_KEY, salt="leiautes-auth-v1")

SENHA_HASH_SOMENTE_PORTAL = ""


def hash_senha(senha: str) -> str:
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def tem_senha_local(senha_hash: str | None) -> bool:
    return bool(senha_hash and senha_hash.strip())


def verificar_senha(senha: str, senha_hash: str | None) -> bool:
    if not tem_senha_local(senha_hash):
        return False
    try:
        return bcrypt.checkpw(senha.encode("utf-8"), str(senha_hash).encode("utf-8"))
    except ValueError:
        return False


def emitir_token_sessao(usuario_id: int) -> str:
    return _serializer.dumps({"uid": usuario_id})


def validar_token_sessao(token: str) -> int | None:
    try:
        payload = _serializer.loads(token, max_age=AUTH_SESSAO_MAX_AGE_SEG)
    except (BadSignature, SignatureExpired):
        return None
    if not isinstance(payload, dict):
        return None
    uid = payload.get("uid")
    return uid if isinstance(uid, int) else None

