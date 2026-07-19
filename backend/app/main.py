"""
SafeMatch API Entrypoint

Responsibilities
----------------
- FastAPI initialization
- middleware registration
- route registration
- startup events
- shutdown events
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import neighborhood as neighborhood_router
from app.api.routes import recommend as recommend_router

app = FastAPI(
    title="SafeMatch API",
    description=(
        "AI-assisted neighborhood recommendation platform "
        "focused on earthquake safety."
    ),
    version="0.1.0",
)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Route registration
# ---------------------------------------------------------------------------

app.include_router(neighborhood_router.router, prefix="/api/v1")
app.include_router(recommend_router.router, prefix="/api/v1")


# ---------------------------------------------------------------------------
# Health / root
# ---------------------------------------------------------------------------

@app.get("/")
async def root():
    return {
        "project": "SafeMatch AI",
        "status": "running",
        "version": "0.1.0",
        "phase": "sprint-3",
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy"
    }