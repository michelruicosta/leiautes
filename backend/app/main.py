# -*- coding: utf-8 -*-
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import API_VERSION
from app.routers import configuracoes, dashboard, execucoes, health, leiautes
from persistencia.db import init_db

app = FastAPI(
    title="leiautes_bacen - API",
    description="Monitoramento de leiautes Bacen e comparacao de versoes - MVP v1.",
    version=API_VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8001",
        "http://127.0.0.1:8002",
        "https://finaudapps.com.br",
        "https://www.finaudapps.com.br",
        "https://admin.finaudapps.com.br",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(dashboard.router)
app.include_router(leiautes.router)
app.include_router(execucoes.router)
app.include_router(configuracoes.router)


@app.on_event("startup")
def _startup() -> None:
    init_db()


def main() -> None:
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()
