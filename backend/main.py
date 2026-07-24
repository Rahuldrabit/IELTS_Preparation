"""
IELTS Tutor Backend - Single FastAPI Application
All services combined into one app with route prefixes
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.config import settings
from services.auth.router import router as auth_router
from services.profile.router import router as profile_router
from services.reading.router import router as reading_router
from services.listening.router import router as listening_router
from services.writing.router import router as writing_router
from services.vocabulary.router import router as vocabulary_router
from services.grammar.router import router as grammar_router
from services.import_svc.router import router as import_router
from services.analytics.router import router as analytics_router
from services.chat.router import router as chat_router
from services.agents.router import router as agents_router
from services.mocktest.router import router as mocktest_router
from services.telemetry.router import router as telemetry_router
from services.speaking.router import router as speaking_router
from services.journey.router import router as journey_router
# Importing the agents package triggers all @registry.register decorators
import services.agents  # noqa: F401
# Scheduler for weekly batch jobs
from shared.scheduler import start_scheduler, shutdown_scheduler, list_scheduled_jobs

from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    print("Starting IELTS Tutor Backend...")
    start_scheduler()
    
    # Register weekly jobs
    from services.analytics.main import register_weekly_error_dna_job
    register_weekly_error_dna_job()
    
    yield
    print("Shutting down IELTS Tutor Backend...")
    shutdown_scheduler()


# Create main FastAPI application
app = FastAPI(
    title="IELTS Tutor API",
    description="AI-Powered IELTS Learning Platform Backend",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handlers
@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error(f"Database error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal database error occurred."},
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again later."},
    )


# Health check
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "ielts-tutor"}


# Scheduler status
@app.get("/scheduler/jobs")
async def scheduler_jobs():
    """List all scheduled jobs."""
    return {"jobs": list_scheduled_jobs()}


# Mount all service routers with /api prefix
app.include_router(auth_router, prefix="/api")
app.include_router(profile_router, prefix="/api")
app.include_router(reading_router, prefix="/api")
app.include_router(listening_router, prefix="/api")
app.include_router(writing_router, prefix="/api")
app.include_router(vocabulary_router, prefix="/api")
app.include_router(grammar_router, prefix="/api")
app.include_router(import_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(agents_router, prefix="/api")
app.include_router(mocktest_router, prefix="/api")
app.include_router(telemetry_router, prefix="/api")
app.include_router(speaking_router, prefix="/api")
app.include_router(journey_router, prefix="/api")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)