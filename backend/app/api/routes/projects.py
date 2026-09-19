import json
import asyncio
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.db import get_db
from app.api.deps import get_current_db_user
from app.models.user import User
from app.models.project import Project, ProjectStatus
from app.models.agent_run import AgentRun
from app.schemas.project import Project as ProjectSchema, ProjectCreate, ProjectUpdate
from app.workers.tasks import run_agentic_pipeline

router = APIRouter()

@router.post("/", response_model=ProjectSchema, status_code=status.HTTP_201_CREATED)
def create_project(
    project_in: ProjectCreate,
    current_user: User = Depends(get_current_db_user),
    db: Session = Depends(get_db)
):
    """
    Creates a new project and triggers the background multi-agent orchestrator.
    """
    project = Project(
        user_id=current_user.id,
        title=project_in.title,
        problem_statement=project_in.problem_statement,
        status=ProjectStatus.QUEUED
    )
    db.add(project)
    try:
        db.commit()
        db.refresh(project)
        
        # Trigger async pipeline worker task (Celery with thread fallback for non-docker/local dev)
        from app.core.config import settings
        if settings.DEV_MODE:
            import threading
            threading.Thread(
                target=run_agentic_pipeline,
                args=(str(project.id), project.problem_statement),
                daemon=True
            ).start()
        else:
            try:
                run_agentic_pipeline.delay(str(project.id), project.problem_statement)
            except Exception:
                import threading
                threading.Thread(
                    target=run_agentic_pipeline,
                    args=(str(project.id), project.problem_statement),
                    daemon=True
                ).start()
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database execution failed: {str(e)}"
        )
        
    return project

@router.get("/", response_model=List[ProjectSchema])
def list_projects(
    current_user: User = Depends(get_current_db_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves all projects owned by the logged-in user.
    """
    return db.query(Project).filter(Project.user_id == current_user.id).order_by(Project.created_at.desc()).all()

@router.get("/{project_id}", response_model=ProjectSchema)
def get_project(
    project_id: UUID,
    current_user: User = Depends(get_current_db_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves details for a single project owned by the user.
    """
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or you do not have permission to access it"
        )
    return project

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: UUID,
    current_user: User = Depends(get_current_db_user),
    db: Session = Depends(get_db)
):
    """
    Deletes a project and all its cascading entities (pages, canvas states).
    """
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or you do not have permission to access it"
        )
        
    try:
        db.delete(project)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete project: {str(e)}"
        )
    return None

@router.get("/{project_id}/status")
def get_project_status_stream(
    project_id: UUID,
    current_user: User = Depends(get_current_db_user),
    db: Session = Depends(get_db)
):
    """
    Server-Sent Events (SSE) endpoint to stream real-time pipeline status updates
    including individual agent execution steps.
    """
    # Enforce access checks before creating connection
    project_exists = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project workspace not found"
        )

    async def event_generator():
        # Clean session per thread loop
        loop_db = Session(bind=db.bind)
        try:
            while True:
                proj = loop_db.query(Project).filter(Project.id == project_id).first()
                if not proj:
                    yield "event: error\ndata: Project deleted\n\n"
                    break
                
                # Fetch latest agent runs tracking data
                runs = loop_db.query(AgentRun).filter(AgentRun.project_id == project_id).all()
                agent_runs_payload = [
                    {
                        "agent_type": r.agent_type,
                        "status": r.status,
                        "tokens_used": r.tokens_used,
                        "latency_ms": r.latency_ms
                    } for r in runs
                ]
                
                state_data = {
                    "project_id": str(project_id),
                    "status": proj.status,
                    "agent_runs": agent_runs_payload
                }
                
                yield f"event: status_update\ndata: {json.dumps(state_data)}\n\n"
                
                if proj.status in [ProjectStatus.DONE, ProjectStatus.FAILED]:
                    break
                    
                await asyncio.sleep(2)
        finally:
            loop_db.close()

    return StreamingResponse(event_generator(), media_type="text/event-stream")
