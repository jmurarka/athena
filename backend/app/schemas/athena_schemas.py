from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class RequirementSchema(BaseModel):
    id: str
    code: str
    title: str
    description: str
    category: str
    priority: str

    class Config:
        from_attributes = True


class FeatureSchema(BaseModel):
    id: str
    code: str
    title: str
    description: str
    user_story: Optional[str] = None
    is_mvp: bool

    class Config:
        from_attributes = True


class ArchitectureComponentSchema(BaseModel):
    id: str
    component_id_name: str
    name: str
    component_type: str
    tech_stack: Optional[str] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True


class DecisionSchema(BaseModel):
    id: str
    topic: str
    chosen_option: str
    why_chosen: str
    why_not_alternatives: Optional[str] = None
    trade_offs: Optional[str] = None
    assumptions: Optional[str] = None

    class Config:
        from_attributes = True


class EvidenceClaimSchema(BaseModel):
    id: str
    claim_text: str
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    status: str

    class Config:
        from_attributes = True


class ValidationIssueSchema(BaseModel):
    id: str
    severity: str
    code: str
    title: str
    description: str
    suggested_fix: Optional[str] = None
    affected_entities: List[str] = []

    class Config:
        from_attributes = True


class ProjectHealthMetricsSchema(BaseModel):
    coverage_score: float = 0.0
    contradiction_rate: float = 0.0
    unsupported_claim_rate: float = 0.0
    critical_count: int = 0
    warning_count: int = 0
    review_count: int = 0
    total_requirements: int = 0
    mapped_requirements: int = 0


class ProjectGraphResponse(BaseModel):
    project_id: str
    health_metrics: ProjectHealthMetricsSchema
    requirements: List[RequirementSchema]
    features: List[FeatureSchema]
    components: List[ArchitectureComponentSchema]
    decisions: List[DecisionSchema]
    evidence_claims: List[EvidenceClaimSchema]
    validation_issues: List[ValidationIssueSchema]


class EditRequirementRequest(BaseModel):
    title: str
    description: str


class EditTechDecisionRequest(BaseModel):
    chosen_option: str


class DocumentIngestRequest(BaseModel):
    filename: str
    content: str
