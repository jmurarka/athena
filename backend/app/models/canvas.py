import uuid
from sqlalchemy import Column, DateTime, ForeignKey, func, Uuid, JSON
from sqlalchemy.orm import relationship
from app.core.db import Base

class CanvasState(Base):
    """
    SQLAlchemy model representing the canvas_states table,
    recording the visual nodes and edges representation for React Flow.
    """
    __tablename__ = "canvas_states"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    project_id = Column(Uuid, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    canvas_json = Column(JSON, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    project = relationship("Project", back_populates="canvas_state")
