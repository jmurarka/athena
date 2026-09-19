import uuid
from uuid import UUID
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.api.deps import get_current_db_user
from app.models.user import User
from app.models.project import Project
from app.models.graph_models import (
    Requirement, Feature, ArchitectureComponent, Decision, EvidenceClaim, ValidationIssue
)
from app.schemas.athena_schemas import (
    ProjectGraphResponse, EditRequirementRequest, EditTechDecisionRequest, DocumentIngestRequest
)
from app.core.impact_analyzer import ImpactAnalyzer
from app.core.rag_service import RAGService

router = APIRouter()

def to_uuid(val):
    if val is None or isinstance(val, UUID):
        return val
    try:
        return uuid.UUID(str(val))
    except Exception:
        return val


@router.get("/{project_id}/graph", response_model=ProjectGraphResponse)
def get_project_graph(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_db_user)
) -> Any:
    """
    Retrieves the complete Requirement and Decision Graph, Validation Issues, and Health Metrics.
    """
    p_uuid = to_uuid(project_id)
    project = db.query(Project).filter(Project.id == p_uuid, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    reqs = db.query(Requirement).filter(Requirement.project_id == p_uuid).all()
    feats = db.query(Feature).filter(Feature.project_id == p_uuid).all()
    comps = db.query(ArchitectureComponent).filter(ArchitectureComponent.project_id == p_uuid).all()
    decs = db.query(Decision).filter(Decision.project_id == p_uuid).all()
    claims = db.query(EvidenceClaim).filter(EvidenceClaim.project_id == p_uuid).all()
    issues = db.query(ValidationIssue).filter(ValidationIssue.project_id == p_uuid).all()

    health_metrics = project.health_metrics or {
        "coverage_score": 0.0,
        "contradiction_rate": 0.0,
        "unsupported_claim_rate": 0.0,
        "critical_count": 0,
        "warning_count": 0,
        "review_count": 0,
        "total_requirements": len(reqs),
        "mapped_requirements": len(reqs)
    }

    return {
        "project_id": str(project.id),
        "health_metrics": health_metrics,
        "requirements": reqs,
        "features": feats,
        "components": comps,
        "decisions": decs,
        "evidence_claims": claims,
        "validation_issues": issues
    }


@router.post("/{project_id}/requirements/{requirement_id}/edit")
def edit_requirement_and_revalidate(
    project_id: UUID,
    requirement_id: str,
    body: EditRequirementRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_db_user)
) -> Any:
    """
    ATHENA Living Blueprint: Modifies requirement, calculates downstream affected entities, and revalidates project.
    """
    p_uuid = to_uuid(project_id)
    project = db.query(Project).filter(Project.id == p_uuid, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    analyzer = ImpactAnalyzer(db)
    result = analyzer.analyze_requirement_change(
        project_id=str(p_uuid),
        requirement_id=requirement_id,
        new_title=body.title,
        new_desc=body.description
    )

    return result


@router.post("/{project_id}/decisions/{decision_id}/edit")
def edit_tech_decision_and_revalidate(
    project_id: UUID,
    decision_id: str,
    body: EditTechDecisionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_db_user)
) -> Any:
    """
    ATHENA Living Blueprint: Updates technology choice, propagates changes across affected components, and revalidates.
    """
    p_uuid = to_uuid(project_id)
    project = db.query(Project).filter(Project.id == p_uuid, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    analyzer = ImpactAnalyzer(db)
    result = analyzer.analyze_tech_decision_change(
        project_id=str(p_uuid),
        decision_id=decision_id,
        new_choice=body.chosen_option
    )

    return result


@router.post("/{project_id}/documents/ingest")
def ingest_document(
    project_id: UUID,
    body: DocumentIngestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_db_user)
) -> Any:
    """
    ATHENA Local RAG: Ingests uploaded research paper or project spec for context retrieval.
    """
    p_uuid = to_uuid(project_id)
    project = db.query(Project).filter(Project.id == p_uuid, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    rag = RAGService(db)
    chunks = rag.ingesting_document(
        project_id=str(p_uuid),
        filename=body.filename,
        content=body.content
    )

    return {"status": "success", "chunks_created": len(chunks)}


@router.get("/{project_id}/documents/search")
def search_documents(
    project_id: UUID,
    query: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_db_user)
) -> Any:
    """
    ATHENA Local RAG: Searches ingested project documents for query context.
    """
    p_uuid = to_uuid(project_id)
    project = db.query(Project).filter(Project.id == p_uuid, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    rag = RAGService(db)
    context = rag.search_context(project_id=str(p_uuid), query=query)
    return {"query": query, "context": context}
