from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from pythonjsonlogger import jsonlogger
import sys

from .config import settings
from .database import db
from .metrics import MetricsMiddleware, get_metrics
from .routes import crud, streaming

# Configure structured logging
logHandler = logging.StreamHandler(sys.stdout)
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logging.basicConfig(level=settings.log_level, handlers=[logHandler])

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting async FastAPI application")
    await db.connect()
    yield
    # Shutdown
    logger.info("Shutting down async FastAPI application")
    await db.close()


app = FastAPI(
    title="Async Cassandra Performance Test",
    description="FastAPI application using async-cassandra client",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add metrics middleware
app.middleware("http")(MetricsMiddleware())

# Include routers
app.include_router(crud.router, prefix="/api/v1", tags=["CRUD"])
app.include_router(streaming.router, prefix="/api/v1", tags=["Streaming"])


@app.get("/health")
async def health_check():
    try:
        # Check Cassandra connectivity
        session = db.get_session()
        if session:
            await session.execute("SELECT now() FROM system.local")
            cassandra_status = "healthy"
        else:
            cassandra_status = "unhealthy"
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        cassandra_status = "unhealthy"
    
    return {
        "status": "healthy" if cassandra_status == "healthy" else "degraded",
        "cassandra": cassandra_status,
        "app_type": "async"
    }


@app.get("/metrics", response_class=Response)
async def metrics():
    metrics_data = await get_metrics()
    return Response(content=metrics_data, media_type="text/plain")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.app_port,
        workers=settings.workers,
        log_config=None
    )