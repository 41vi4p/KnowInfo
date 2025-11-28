"""
KnowInfo - Crisis Misinformation Detection System
Main FastAPI Application
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from contextlib import asynccontextmanager
import structlog

from config import settings
from src.database.mongodb import init_mongo, mongo_manager
from src.database.neo4j_db import init_neo4j, neo4j_manager
from src.database.redis_cache import init_redis, redis_manager
from src.utils.logger import setup_logging
from src.utils.model_manager import init_model_manager
from src.utils.metrics import get_metrics

# Import API routers (to be created)
# from src.api.whatsapp import router as whatsapp_router
# from src.api.dashboard import router as dashboard_router
# from src.api.public import router as public_router

logger = setup_logging(settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("Starting KnowInfo system", environment=settings.environment)

    # Initialize databases
    try:
        await init_mongo(settings.mongodb_uri, settings.mongodb_db_name)
        logger.info("MongoDB initialized")
    except Exception as e:
        logger.error("MongoDB initialization failed", error=str(e))

    try:
        await init_neo4j(settings.neo4j_uri, settings.neo4j_user, settings.neo4j_password)
        logger.info("Neo4j initialized")
    except Exception as e:
        logger.error("Neo4j initialization failed", error=str(e))

    try:
        await init_redis(settings.redis_url)
        logger.info("Redis initialized")
    except Exception as e:
        logger.error("Redis initialization failed", error=str(e))

    # Initialize model manager
    init_model_manager(
        ollama_base_url=settings.ollama_base_url,
        gemini_api_key=settings.gemini_api_key,
        openai_api_key=settings.openai_api_key,
        anthropic_api_key=settings.anthropic_api_key,
        use_local_first=settings.use_local_models_first
    )
    logger.info("Model manager initialized")

    yield

    # Shutdown
    logger.info("Shutting down KnowInfo system")
    if mongo_manager:
        await mongo_manager.disconnect()
    if neo4j_manager:
        await neo4j_manager.disconnect()
    if redis_manager:
        await redis_manager.disconnect()


# Create FastAPI app
app = FastAPI(
    title="KnowInfo - Crisis Misinformation Detection",
    description="Real-time misinformation detection and verification system",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "KnowInfo - Crisis Misinformation Detection",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "api_docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health = {
        "status": "healthy",
        "components": {}
    }

    # Check MongoDB
    try:
        if mongo_manager:
            await mongo_manager.client.admin.command('ping')
            health["components"]["mongodb"] = "healthy"
        else:
            health["components"]["mongodb"] = "not_initialized"
    except Exception as e:
        health["components"]["mongodb"] = f"unhealthy: {str(e)}"
        health["status"] = "degraded"

    # Check Neo4j
    try:
        if neo4j_manager and neo4j_manager.driver:
            async with neo4j_manager.driver.session() as session:
                await session.run("RETURN 1")
            health["components"]["neo4j"] = "healthy"
        else:
            health["components"]["neo4j"] = "not_initialized"
    except Exception as e:
        health["components"]["neo4j"] = f"unhealthy: {str(e)}"
        health["status"] = "degraded"

    # Check Redis
    try:
        if redis_manager and redis_manager.client:
            await redis_manager.client.ping()
            health["components"]["redis"] = "healthy"
        else:
            health["components"]["redis"] = "not_initialized"
    except Exception as e:
        health["components"]["redis"] = f"unhealthy: {str(e)}"
        health["status"] = "degraded"

    return health


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=get_metrics(), media_type="text/plain")


# Include API routers
# app.include_router(whatsapp_router, prefix="/api/whatsapp", tags=["WhatsApp"])
# app.include_router(dashboard_router, prefix="/api/dashboard", tags=["Dashboard"])
# app.include_router(public_router, prefix="/api/v1", tags=["Public API"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.api_port,
        reload=settings.environment == "development"
    )
