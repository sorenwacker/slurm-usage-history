from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import admin, dashboard, data, saml
from .core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="API for Slurm Usage History Dashboard with data ingestion capabilities",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(data.router, prefix=f"{settings.api_prefix}/data", tags=["Data Ingestion"])
app.include_router(dashboard.router, prefix=f"{settings.api_prefix}/dashboard", tags=["Dashboard"])
app.include_router(admin.router, prefix=f"{settings.api_prefix}/admin", tags=["Admin"])
app.include_router(saml.router, prefix="/saml", tags=["SAML Authentication"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Slurm Usage History API",
        "version": settings.api_version,
        "docs": "/docs",
    }


@app.get("/api")
async def api_info():
    """API information."""
    return {
        "title": settings.api_title,
        "version": settings.api_version,
        "endpoints": {
            "data_ingestion": f"{settings.api_prefix}/data/ingest",
            "health": f"{settings.api_prefix}/dashboard/health",
            "metadata": f"{settings.api_prefix}/dashboard/metadata",
            "filter": f"{settings.api_prefix}/dashboard/filter",
            "stats": f"{settings.api_prefix}/dashboard/stats/{{hostname}}",
        },
    }
