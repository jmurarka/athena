from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Dict, Any

class CanvasStateBase(BaseModel):
    canvas_json: Dict[str, Any] = Field(
        default_factory=dict,
        description="Structured nodes and edges layout for React Flow rendering"
    )

class CanvasStateCreate(CanvasStateBase):
    pass

class CanvasStateUpdate(CanvasStateBase):
    pass

class CanvasState(CanvasStateBase):
    id: UUID
    project_id: UUID
    updated_at: datetime

    class Config:
        from_attributes = True
