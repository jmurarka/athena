from fastapi import APIRouter
from app.api.routes.projects import router as projects_router
from app.api.routes.pages import router as pages_router
from app.api.routes.canvas import router as canvas_router

api_router = APIRouter()

# Register sub-routers with logical prefixes
api_router.include_router(projects_router, prefix="/projects", tags=["projects"])
api_router.include_router(pages_router, prefix="/projects", tags=["pages"])
api_router.include_router(canvas_router, prefix="/projects", tags=["canvas"])
