from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional
from app.models.project import ProjectStatus

class ProjectBase(BaseModel):
    title: str = Field(..., max_length=255, description="Short descriptive title of the project")
    problem_statement: str = Field(..., description="Raw unstructured problem description")

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    problem_statement: Optional[str] = None
    status: Optional[ProjectStatus] = None

class Project(ProjectBase):
    id: UUID
    user_id: UUID
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
