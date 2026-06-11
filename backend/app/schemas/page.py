from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any
from app.models.page import AgentType

class PageBase(BaseModel):
    title: str = Field(..., max_length=255)
    content_json: Dict[str, Any] = Field(default_factory=dict, description="Notion-style structured text blocks")

class PageCreate(PageBase):
    agent_type: AgentType

class PageUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    content_json: Optional[Dict[str, Any]] = None

class Page(PageBase):
    id: UUID
    project_id: UUID
    agent_type: AgentType
    version: int
    updated_at: datetime

    class Config:
        from_attributes = True
