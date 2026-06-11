import uuid
import enum
from sqlalchemy import Column, DateTime, ForeignKey, func, Enum as SQLEnum, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.db import Base
from app.models.page import AgentType

class AgentRunStatus(str, enum.Enum):
    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"

class AgentRun(Base):
    """
    SQLAlchemy model representing individual agent executions,
    storing token metrics, execution latencies, and error codes.
    """
    __tablename__ = "agent_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_type = Column(SQLEnum(AgentType, name="agent_type"), nullable=False, index=True)
    status = Column(
        SQLEnum(AgentRunStatus, name="agent_run_status"),
        nullable=False
    )
    tokens_used = Column(Integer, default=0, nullable=False)
    latency_ms = Column(Integer, default=0, nullable=False)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    project = relationship("Project", back_populates="agent_runs")
