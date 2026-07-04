"""
SafeMatch API Entrypoint

Responsibilities
----------------
- FastAPI initialization
- middleware registration
- route registration
- startup events
- shutdown events

Sprint Status
-------------
Architecture phase only.
Implementation planned for Sprint 3.
"""
from fastapi import FastAPI


app = FastAPI(
    title="SafeMatch API",
    description=(
        "AI-assisted neighborhood recommendation platform "
        "focused on earthquake safety."
    ),
    version="0.1.0",
)


@app.get("/")
async def root():
    return {
        "project": "SafeMatch AI",
        "status": "running",
        "version": "0.1.0",
        "phase": "project scaffold",
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy"
    }