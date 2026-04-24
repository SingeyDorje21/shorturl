"""
Shortener Service (port 8001)
-----------------------------
Handles URL creation and stats lookups.
Internal only — not exposed to the public internet; gateway proxies to it.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from shared.app.config import get_settings
from shared.app.db.session import init_db
from shared.app.schemas import HealthResponse
from shortener.app.routes import router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[Shortener] initialising database...")
    await init_db()
    print("[Shortener] ready")
    yield
    print("[Shortener] shut down")


app = FastAPI(
    title="Short URL — Shortener Service",
    version=settings.VERSION,
    lifespan=lifespan,
)

@app.get("/health", response_model=HealthResponse, tags=["meta"])
async def health():
    return HealthResponse(service="shortener", version=settings.VERSION)


app.include_router(router)
