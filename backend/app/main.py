# -*- coding: utf-8 -*-
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import API_VERSION, CORS_ALLOW_ORIGINS, ENVIRONMENT
from app.routers import (
    alteracoes,
    auth,
    auditoria,
    configuracoes,
    dashboard,
    execucoes,
    health,
    leiautes,
    relatorios,
    robo,
    usuarios,
    versoes,
)
from persistencia.db import init_db

# A01-9: /docs e /openapi.json só em desenvolvimento
_docs_url = None if ENVIRONMENT == "production" else "/docs"
_redoc_url = None if ENVIRONMENT == "production" else "/redoc"
_openapi_url = None if ENVIRONMENT == "production" else "/openapi.json"

app = FastAPI(
    title="leiautes_bacen - API",
    description="Monitoramento de leiautes Bacen e comparacao de versoes - MVP v1.",
    version=API_VERSION,
    docs_url=_docs_url,
    redoc_url=_redoc_url,
    openapi_url=_openapi_url,
)

# A01-13: origens CORS vindas do .env (sem localhost em produção)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(leiautes.router)
app.include_router(alteracoes.router)
app.include_router(auditoria.router)
app.include_router(execucoes.router)
app.include_router(configuracoes.router)
app.include_router(robo.router)
app.include_router(usuarios.router)
app.include_router(relatorios.router)
app.include_router(versoes.router)


@app.on_event("startup")
def _startup() -> None:
    init_db()


def main() -> None:
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8003,
        reload=True,
    )


if __name__ == "__main__":
    main()
