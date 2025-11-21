"""
FastAPI Backend for Career Sequence Game
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from contextlib import asynccontextmanager
import asyncio
import os
import logging

from app.config import get_settings, setup_logging
from app.routers import game, player, session
from app.dependencies import get_session_service
from app.middleware import rate_limit_handler

# Initialize logging
logger = setup_logging()

settings = get_settings()

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Background task for session cleanup
async def cleanup_sessions_task():
    """Background task to cleanup expired sessions periodically"""
    while True:
        try:
            await asyncio.sleep(settings.session_cleanup_interval)
            session_service = get_session_service()
            cleaned = session_service.cleanup_expired_sessions()
            if cleaned > 0:
                logger.info(f"Cleaned up {cleaned} expired sessions")
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}", exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for the application"""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Database path: {settings.database_path}")
    logger.info(f"CORS origins: {settings.get_cors_origins()}")
    
    # Check database exists
    if not os.path.exists(settings.database_path):
        logger.warning(f"Database not found at {settings.database_path}")
        logger.warning("Please run the data collection scripts first")
    else:
        logger.info(f"Database found: {settings.database_path}")
    
    # Start background cleanup task
    cleanup_task = asyncio.create_task(cleanup_sessions_task())
    logger.info("Started session cleanup background task")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    logger.info("Cleanup task stopped")

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API for the Career Sequence guessing game",
    lifespan=lifespan
)

# Add rate limiter state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

# Configure CORS - use parsed origins
cors_origins = settings.get_cors_origins()
logger.info(f"Configuring CORS with origins: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create static directory if it doesn't exist
os.makedirs("static/images/players", exist_ok=True)
os.makedirs("static/images/clubs", exist_ok=True)
os.makedirs("static/images/placeholders", exist_ok=True)

# Mount static files for images
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(game.router)
app.include_router(player.router)
app.include_router(session.router)


@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "message": settings.app_name,
        "status": "running",
        "version": settings.app_version,
        "environment": settings.environment
    }


@app.get("/health")
def health_check():
    """Health check endpoint for monitoring"""
    db_exists = os.path.exists(settings.database_path)
    return {
        "status": "healthy" if db_exists else "degraded",
        "database": "connected" if db_exists else "not found",
        "environment": settings.environment
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level=settings.log_level.lower()
    )