from celery import Celery
from app.core.config import settings

# Initialize Celery app with Redis broker and backend
celery = Celery(
    "agentic_planner_workers",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

# Configuration updates
celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Auto-discover task imports
    imports=["app.workers.tasks"]
)
