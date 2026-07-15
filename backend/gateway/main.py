"""API Gateway - Single entry point that proxies to all microservices."""
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import httpx

from shared import settings


# Service URLs (service name -> URL)
SERVICES = {
    "profile": "http://profile:8001",
    "reading": "http://reading:8002",
    "listening": "http://listening:8003",
    "writing": "http://writing:8004",
    "vocabulary": "http://vocabulary:8005",
    "grammar": "http://grammar:8006",
    "import": "http://import_svc:8007",
    "analytics": "http://analytics:8008",
    "agent": "http://ai_agent:8009",
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup: verify all services are reachable
    async with httpx.AsyncClient(timeout=5.0) as client:
        for name, url in SERVICES.items():
            try:
                await client.get(f"{url}/health")
                print(f"✓ {name} service is healthy")
            except Exception as e:
                print(f"✗ {name} service is not reachable: {e}")
    yield
    # Shutdown: cleanup


app = FastAPI(
    title="IELTS Tutor API Gateway",
    description="Single entry point for all backend services",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware - allow frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# HTTP client for proxying
http_client: httpx.AsyncClient | None = None


@app.on_event("startup")
async def startup():
    """Initialize HTTP client on startup."""
    global http_client
    http_client = httpx.AsyncClient(timeout=60.0)


@app.on_event("shutdown")
async def shutdown():
    """Close HTTP client on shutdown."""
    if http_client:
        await http_client.aclose()


async def proxy_request(request: Request, service: str, path: str) -> Response:
    """Proxy a request to the specified service."""
    if not http_client:
        return Response(
            content='{"error": "Gateway not initialized"}',
            status_code=500,
            media_type="application/json",
        )

    service_url = SERVICES.get(service)
    if not service_url:
        return Response(
            content=f'{{"error": "Unknown service: {service}"}}',
            status_code=404,
            media_type="application/json",
        )

    # Build target URL
    target_url = f"{service_url}/{path}"

    # Forward the request
    try:
        # Get request body if present
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()

        # Forward headers (except host)
        headers = dict(request.headers)
        headers.pop("host", None)

        # Make the proxied request
        response = await http_client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=body,
            params=request.query_params,
        )

        return Response(
            content=response.content,
            status_code=response.status_code,
            media_type=response.headers.get("content-type", "application/json"),
        )
    except httpx.ConnectError:
        return Response(
            content=f'{{"error": "Service {service} is not available"}}',
            status_code=503,
            media_type="application/json",
        )
    except Exception as e:
        return Response(
            content=f'{{"error": "Proxy error: {str(e)}"}}',
            status_code=500,
            media_type="application/json",
        )


# ============ Route Handlers ============


@app.get("/health")
async def health_check():
    """Gateway health check."""
    return {"status": "ok", "service": "gateway"}


# Profile routes
@app.api_route("/api/profile/{path:path}", methods=["GET", "PUT", "PATCH", "DELETE"])
async def profile_proxy(request: Request, path: str):
    return await proxy_request(request, "profile", path)


# Reading routes
@app.api_route("/api/reading/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def reading_proxy(request: Request, path: str):
    return await proxy_request(request, "reading", path)


# Listening routes
@app.api_route("/api/listening/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def listening_proxy(request: Request, path: str):
    return await proxy_request(request, "listening", path)


# Writing routes
@app.api_route("/api/writing/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def writing_proxy(request: Request, path: str):
    return await proxy_request(request, "writing", path)


# Vocabulary routes
@app.api_route("/api/vocabulary/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def vocabulary_proxy(request: Request, path: str):
    return await proxy_request(request, "vocabulary", path)


# Grammar routes
@app.api_route("/api/grammar/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def grammar_proxy(request: Request, path: str):
    return await proxy_request(request, "grammar", path)


# Import routes
@app.api_route("/api/import/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def import_proxy(request: Request, path: str):
    return await proxy_request(request, "import", path)


# Analytics routes
@app.api_route("/api/analytics/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def analytics_proxy(request: Request, path: str):
    return await proxy_request(request, "analytics", path)


# AI Agent routes
@app.api_route("/api/agent/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def agent_proxy(request: Request, path: str):
    return await proxy_request(request, "agent", path)


# Static audio files for listening
@app.get("/api/listening/audio/{filename}")
async def get_audio(filename: str):
    """Serve audio files from listening service."""
    return await proxy_request(
        Request(
            scope={
                "type": "http.request",
                "method": "GET",
                "path": f"/audio/{filename}",
                "query_string": b"",
                "headers": [],
            }
        ),
        "listening",
        f"audio/{filename}",
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)