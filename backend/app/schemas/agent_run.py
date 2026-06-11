from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional
from app.models.page import AgentType
from app.models.agent_run import AgentRunStatus

class AgentRunBase(BaseModel):
    agent_type: AgentType
    status: AgentRunStatus
    tokens_used: int = Field(default=0, ge=0)
    latency_ms: int = Field(default=0, ge=0)
    error: Optional[str] = None

class AgentRunCreate(AgentRunBase):
    pass

class AgentRunUpdate(BaseModel):
    status: Optional[AgentRunStatus] = None
    tokens_used: Optional[int] = Field(None, ge=0)
    latency_ms: Optional[int] = Field(None, ge=0)
    error: Optional[str] = None

class AgentRun(AgentRunBase):
    id: UUID
    project_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
