import uuid
import enum
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, func, Enum as SQLEnum, Uuid, JSON
from sqlalchemy.orm import relationship
from app.core.db import Base

class ProjectStatus(str, enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"

class Project(Base):
    """
    SQLAlchemy model representing the 'projects' table,
    recording problem statements and orchestration status.
    """
    __tablename__ = "projects"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    problem_statement = Column(Text, nullable=False)
    status = Column(
        SQLEnum(ProjectStatus, name="project_status"),
        default=ProjectStatus.QUEUED,
        nullable=False,
        index=True
    )
    health_metrics = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="projects")
    pages = relationship("Page", back_populates="project", cascade="all, delete-orphan")
    canvas_state = relationship("CanvasState", back_populates="project", uselist=False, cascade="all, delete-orphan")
    agent_runs = relationship("AgentRun", back_populates="project", cascade="all, delete-orphan")
    
    # ATHENA Graph Relationships
    requirements = relationship("Requirement", back_populates="project", cascade="all, delete-orphan")
    features = relationship("Feature", back_populates="project", cascade="all, delete-orphan")
    components = relationship("ArchitectureComponent", back_populates="project", cascade="all, delete-orphan")
    decisions = relationship("Decision", back_populates="project", cascade="all, delete-orphan")
    evidence_claims = relationship("EvidenceClaim", back_populates="project", cascade="all, delete-orphan")
    validation_issues = relationship("ValidationIssue", back_populates="project", cascade="all, delete-orphan")
    document_chunks = relationship("DocumentChunk", back_populates="project", cascade="all, delete-orphan")

