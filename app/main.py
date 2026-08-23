from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.api.v1 import restaurants, audits

app = FastAPI(
    title="Restaurant SEO Audit API",
    description="Phase 1: Deterministic SEO audit engine",
    version="0.1.0",
)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return JSONResponse({"status": "ok"})


# Include routers
app.include_router(restaurants.router)
app.include_router(audits.router)
