"""
API Gateway (port 8000)
-----------------------
Single public entry point.  Proxies:
  POST /shorten          → Shortener service
  GET  /{code}/info      → Shortener service
  GET  /{code}           → Redirect service

All CORS handling lives here so downstream services don't need it.
"""

import httpx
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from shared.app.config import get_settings
from shared.app.schemas import HealthResponse

settings = get_settings()

# ---------------------------------------------------------------------------
# Shared async HTTP client — reused across requests (connection pooling)
# ---------------------------------------------------------------------------
_client: httpx.AsyncClient | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _client
    _client = httpx.AsyncClient(timeout=10.0)
    print(f"[Gateway] started — forwarding to shortener={settings.SHORTENER_BASE_URL} redirect={settings.REDIRECT_BASE_URL}")
    yield
    await _client.aclose()
    print("[Gateway] shut down")


app = FastAPI(
    title="Short URL — API Gateway",
    version=settings.VERSION,
    lifespan=lifespan,
    # Hide downstream docs from gateway swagger (optional)
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _proxy(request: Request, url: str) -> Response:
    """Forward a request to a downstream service and return its response."""
    assert _client is not None, "HTTP client not initialised"

    body = await request.body()
    headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in ("host", "content-length")
    }

    try:
        upstream = await _client.request(
            method=request.method,
            url=url,
            content=body,
            headers=headers,
            params=request.query_params,
        )
    except httpx.ConnectError as exc:
        raise HTTPException(status_code=503, detail=f"Upstream service unavailable: {exc}")
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Upstream service timed out")

    # Stream the upstream response back (preserve status, headers, body)
    excluded = {"content-encoding", "transfer-encoding", "connection"}
    response_headers = {
        k: v for k, v in upstream.headers.items()
        if k.lower() not in excluded
    }
    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=response_headers,
        media_type=upstream.headers.get("content-type"),
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse, tags=["meta"])
async def health():
    return HealthResponse(service="gateway", version=settings.VERSION)


@app.post("/shorten", tags=["urls"])
async def shorten(request: Request):
    """Proxy URL creation to the Shortener service."""
    return await _proxy(request, f"{settings.SHORTENER_BASE_URL}/shorten")


@app.get("/{short_code}/info", tags=["urls"])
async def url_info(short_code: str, request: Request):
    """Proxy stats lookup to the Shortener service."""
    return await _proxy(request, f"{settings.SHORTENER_BASE_URL}/{short_code}/info")


@app.get("/{short_code}", tags=["urls"])
async def redirect(short_code: str, request: Request):
    """Proxy redirect to the Redirect service."""
    return await _proxy(request, f"{settings.REDIRECT_BASE_URL}/{short_code}")
