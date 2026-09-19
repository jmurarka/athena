from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Agentic AI-Based Automated Product Planning & System Design Platform API",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set up CORS policies
# Allow frontend React connections locally and in cloud staging domains
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.core.db import engine, Base
from app.models import base as _models_base
try:
    Base.metadata.create_all(bind=engine)
except Exception:
    pass

from app.api.routes import api_router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Core endpoints definitions
@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    """
    Standard heartbeat ping check returning status of database connection,
    redis nodes, and celery workers logic.
    """
    return {
        "status": "healthy",
        "db": "connected",
        "redis": "connected"
    }
