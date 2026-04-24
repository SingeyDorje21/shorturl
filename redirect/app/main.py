"""
Redirect Service (port 8002)
-----------------------------
Hot-path: resolves short codes and issues 307 redirects.
Read-heavy; intentionally kept lean.
Internal only — gateway proxies to it.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from shared.app.config import get_settings
from shared.app.db.session import init_db
from shared.app.schemas import HealthResponse
from redirect.app.routes import router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[Redirect] initialising database...")
    await init_db()
    print("[Redirect] ready")
    yield
    print("[Redirect] shut down")


app = FastAPI(
    title="Short URL — Redirect Service",
    version=settings.VERSION,
    lifespan=lifespan,
)

@app.get("/health", response_model=HealthResponse, tags=["meta"])
async def health():
    return HealthResponse(service="redirect", version=settings.VERSION)


# Wildcard route MUST be registered last so /health isn't swallowed
app.include_router(router)
