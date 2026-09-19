import uuid
import enum
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Float, Boolean, func, Enum as SQLEnum, Uuid, JSON
UUID = Uuid
JSONB = JSON
from sqlalchemy.orm import relationship
from app.core.db import Base


class RequirementCategory(str, enum.Enum):
    FUNCTIONAL = "functional"
    NON_FUNCTIONAL = "non_functional"
    CONSTRAINT = "constraint"


class VerificationStatus(str, enum.Enum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    CONTRADICTED = "contradicted"


class IssueSeverity(str, enum.Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    REVIEW = "review"


class Requirement(Base):
    __tablename__ = "requirements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(50), nullable=False) # e.g. REQ-001
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(SQLEnum(RequirementCategory, name="requirement_category"), default=RequirementCategory.FUNCTIONAL, nullable=False)
    priority = Column(String(50), default="high") # high, medium, low
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    project = relationship("Project", back_populates="requirements")
    features = relationship("FeatureRequirementMapping", back_populates="requirement", cascade="all, delete-orphan")


class Feature(Base):
    __tablename__ = "features"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(50), nullable=False) # e.g. F-001
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    user_story = Column(Text, nullable=True)
    is_mvp = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    project = relationship("Project", back_populates="features")
    requirements = relationship("FeatureRequirementMapping", back_populates="feature", cascade="all, delete-orphan")
    components = relationship("ComponentFeatureMapping", back_populates="feature", cascade="all, delete-orphan")


class FeatureRequirementMapping(Base):
    __tablename__ = "feature_requirement_mappings"

    feature_id = Column(UUID(as_uuid=True), ForeignKey("features.id", ondelete="CASCADE"), primary_key=True)
    requirement_id = Column(UUID(as_uuid=True), ForeignKey("requirements.id", ondelete="CASCADE"), primary_key=True)

    feature = relationship("Feature", back_populates="requirements")
    requirement = relationship("Requirement", back_populates="features")


class ArchitectureComponent(Base):
    __tablename__ = "architecture_components"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    component_id_name = Column(String(100), nullable=False) # e.g. auth_service, postgres_db
    name = Column(String(255), nullable=False)
    component_type = Column(String(100), nullable=False) # api_gateway, database, worker, auth_service, frontend, cache
    tech_stack = Column(String(255), nullable=True) # e.g. PostgreSQL, Redis, FastAPI
    description = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    project = relationship("Project", back_populates="components")
    features = relationship("ComponentFeatureMapping", back_populates="component", cascade="all, delete-orphan")


class ComponentFeatureMapping(Base):
    __tablename__ = "component_feature_mappings"

    component_id = Column(UUID(as_uuid=True), ForeignKey("architecture_components.id", ondelete="CASCADE"), primary_key=True)
    feature_id = Column(UUID(as_uuid=True), ForeignKey("features.id", ondelete="CASCADE"), primary_key=True)

    component = relationship("ArchitectureComponent", back_populates="features")
    feature = relationship("Feature", back_populates="components")


class Decision(Base):
    __tablename__ = "decisions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    topic = Column(String(255), nullable=False) # e.g. Database Selection, Auth Mechanism
    chosen_option = Column(String(255), nullable=False)
    why_chosen = Column(Text, nullable=False)
    why_not_alternatives = Column(Text, nullable=True)
    trade_offs = Column(Text, nullable=True)
    assumptions = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    project = relationship("Project", back_populates="decisions")
    evidence_claims = relationship("EvidenceClaim", back_populates="decision", cascade="all, delete-orphan")


class EvidenceClaim(Base):
    __tablename__ = "evidence_claims"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    decision_id = Column(UUID(as_uuid=True), ForeignKey("decisions.id", ondelete="CASCADE"), nullable=True)
    claim_text = Column(Text, nullable=False)
    source_name = Column(String(255), nullable=True)
    source_url = Column(String(500), nullable=True)
    status = Column(SQLEnum(VerificationStatus, name="verification_status"), default=VerificationStatus.UNVERIFIED, nullable=False)
    checked_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    project = relationship("Project", back_populates="evidence_claims")
    decision = relationship("Decision", back_populates="evidence_claims")


class ValidationIssue(Base):
    __tablename__ = "validation_issues"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    severity = Column(SQLEnum(IssueSeverity, name="issue_severity"), nullable=False) # critical, warning, review
    code = Column(String(50), nullable=False) # e.g. VAL-MISSING-AUTH
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    suggested_fix = Column(Text, nullable=True)
    affected_entities = Column(JSONB, default=list, nullable=False) # list of entity codes/IDs

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    project = relationship("Project", back_populates="validation_issues")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    metadata_json = Column(JSONB, default=dict, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    project = relationship("Project", back_populates="document_chunks")
