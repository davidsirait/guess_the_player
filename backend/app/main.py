"""
FastAPI Backend for Career Sequence Game
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from contextlib import asynccontextmanager
import asyncio

from app.config import get_settings
from app.routers import game, player, session
from app.dependencies import get_session_service

settings = get_settings()

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

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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