"""RetailFlow E-Commerce main application entrypoint."""

from contextlib import asynccontextmanager
from typing import Any
from fastapi import Depends, FastAPI, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.app import __version__
from src.app.core.config import get_settings
from src.app.core.database import close_db_connection, get_db

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação (startup e shutdown)."""
    # Startup: Recursos e inicializações
    yield
    # Shutdown: Liberação graciosa das conexões do banco de dados
    await close_db_connection()


app = FastAPI(
    title=settings.APP_NAME,
    version=__version__,
    description="E-commerce web application with FastAPI, PostgreSQL, and Jinja2.",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG or settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.DEBUG or settings.ENVIRONMENT != "production" else None,
)


@app.get("/", tags=["Root"])
async def root() -> dict[str, str]:
    """Rota raiz com informações básicas da aplicação."""
    return {
        "app": settings.APP_NAME,
        "version": __version__,
        "status": "online",
        "docs": "/docs",
    }


@app.get(
    "/health",
    status_code=status.HTTP_200_OK,
    tags=["Health"],
    summary="Verificação de saúde da aplicação e conectividade com o banco",
)
async def health_check(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Endpoint de verificação de saúde da aplicação."""
    db_status = "connected"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "unavailable"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "app": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "version": __version__,
        "database": db_status,
    }
