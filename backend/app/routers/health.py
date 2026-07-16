# -*- coding: utf-8 -*-
from __future__ import annotations

from fastapi import APIRouter

from app.config import API_VERSION
from app.models.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok", version=API_VERSION)
