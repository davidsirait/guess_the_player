"""
FastAPI Backend for Career Sequence Game
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from contextlib import asynccontextmanager
import asyncio
import os

from app.config import get_settings
from app.routers import game, player, session
from app.dependencies import get_session_service

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
                print(f"Cleaned up {cleaned} expired sessions")
        except Exception as e:
            print(f"Error in cleanup task: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for the application"""
    # Startup: Start background cleanup task
    cleanup_task = asyncio.create_task(cleanup_sessions_task())
    yield
    # Shutdown: Cancel cleanup task
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API for the Career Sequence guessing game",
    lifespan=lifespan
)

# Add rate limiter state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS - use parsed origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
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
        "version": settings.app_version
    }


@app.get("/health")
def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)