from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
import structlog

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.database import engine
from app.db.base import Base
from app.api import batch, simulation, metrics

logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up microservice...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.error("Failed to initialize database tables.", error=str(e))
    yield
    logger.info("Shutting down microservice...")

configure_logging()
settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
)

@app.exception_handler(ValueError)
async def value_error_exception_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )

app.include_router(batch.router)
app.include_router(simulation.router)
app.include_router(metrics.router)

@app.get("/")
async def root():
    return {
        "service": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "status": "running",
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
    }