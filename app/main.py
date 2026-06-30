from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import references_router, runs_router
from app.config import settings
from app.database import async_session
from app.services.minio_service import MinioService

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
    logger.info("Starting Genomics Pipeline API")
    yield
    logger.info("Shutting down Genomics Pipeline API")


origins = [
    f"https://{settings.domain}",
    "http://localhost:5173",
    "http://localhost:8000",
]

app = FastAPI(
    title="Genomics Pipeline",
    description="WGS Germline Variant Calling Pipeline — GATK Best Practices",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(runs_router)
app.include_router(references_router)


@app.get("/health")
async def health() -> dict[str, object]:
    sub_checks: dict[str, str] = {}
    status = "ok"

    try:
        async with async_session() as session:
            from sqlalchemy import text
            await session.execute(text("SELECT 1"))
        sub_checks["database"] = "ok"
    except Exception as exc:
        sub_checks["database"] = f"error: {exc}"
        status = "degraded"

    try:
        mc = MinioService()
        await mc.object_exists("raw", "health-check-probe")
        sub_checks["minio"] = "ok"
    except Exception as exc:
        sub_checks["minio"] = f"error: {exc}"
        status = "degraded"

    return {
        "status": status,
        "timestamp": datetime.now(UTC).isoformat(),
        "checks": sub_checks,
    }
