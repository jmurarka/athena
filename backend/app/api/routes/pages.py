from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.db import get_db
from app.api.deps import get_current_db_user
from app.models.user import User
from app.models.project import Project
from app.models.page import Page, AgentType
from app.schemas.page import Page as PageSchema, PageUpdate

router = APIRouter()

def _get_project_and_verify_ownership(
    project_id: UUID,
    user_id: UUID,
    db: Session
) -> Project:
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == user_id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project workspace not found or you do not have permission"
        )
    return project

@router.get("/{project_id}/pages", response_model=List[PageSchema])
def list_project_pages(
    project_id: UUID,
    current_user: User = Depends(get_current_db_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves all pages generated or created under the specified project.
    """
    _get_project_and_verify_ownership(project_id, current_user.id, db)
    return db.query(Page).filter(Page.project_id == project_id).all()

@router.get("/{project_id}/pages/{agent_type}", response_model=PageSchema)
def get_project_page(
    project_id: UUID,
    agent_type: AgentType,
    current_user: User = Depends(get_current_db_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves a single document page by agent type.
    """
    _get_project_and_verify_ownership(project_id, current_user.id, db)
    
    page = db.query(Page).filter(
        Page.project_id == project_id,
        Page.agent_type == agent_type
    ).first()
    
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document page for agent type '{agent_type}' was not found in this project"
        )
    return page

@router.put("/{project_id}/pages/{agent_type}", response_model=PageSchema)
def update_project_page(
    project_id: UUID,
    agent_type: AgentType,
    page_in: PageUpdate,
    current_user: User = Depends(get_current_db_user),
    db: Session = Depends(get_db)
):
    """
    Updates page content (user modifications) and increments document version.
    """
    _get_project_and_verify_ownership(project_id, current_user.id, db)
    
    page = db.query(Page).filter(
        Page.project_id == project_id,
        Page.agent_type == agent_type
    ).first()
    
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document page for agent type '{agent_type}' was not found"
        )
        
    try:
        if page_in.title is not None:
            page.title = page_in.title
        if page_in.content_json is not None:
            page.content_json = page_in.content_json
        
        # Increment document modification version
        page.version += 1
        
        db.commit()
        db.refresh(page)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update document page contents: {str(e)}"
        )
        
    return page
