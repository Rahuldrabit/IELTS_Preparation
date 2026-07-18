"""
IELTS Tutor Backend - Single FastAPI Application
All services combined into one app with route prefixes
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.profile.main import router as profile_router
from services.reading.main import router as reading_router
from services.listening.main import router as listening_router
from services.writing.main import router as writing_router
from services.vocabulary.main import router as vocabulary_router
from services.grammar.main import router as grammar_router
from services.import_svc.main import router as import_router
from services.analytics.main import router as analytics_router
from services.ai_agent.main import router as ai_agent_router
from services.agents.router import router as agents_router
from services.mocktest.main import router as mocktest_router
from services.telemetry.main import router as telemetry_router
# Importing the agents package triggers all @registry.register decorators
import services.agents  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    print("Starting IELTS Tutor Backend...")
    yield
    print("Shutting down IELTS Tutor Backend...")


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
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "ielts-tutor"}


# Mount all service routers with /api prefix
app.include_router(profile_router, prefix="/api")
app.include_router(reading_router, prefix="/api")
app.include_router(listening_router, prefix="/api")
app.include_router(writing_router, prefix="/api")
app.include_router(vocabulary_router, prefix="/api")
app.include_router(grammar_router, prefix="/api")
app.include_router(import_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(ai_agent_router, prefix="/api")
app.include_router(agents_router, prefix="/api")
app.include_router(mocktest_router, prefix="/api")
app.include_router(telemetry_router, prefix="/api")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)