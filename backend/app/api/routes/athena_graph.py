from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.api.deps import get_current_user
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


@router.get("/{project_id}/graph", response_model=ProjectGraphResponse)
def get_project_graph(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Retrieves the complete Requirement and Decision Graph, Validation Issues, and Health Metrics.
    """
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    reqs = db.query(Requirement).filter(Requirement.project_id == project_id).all()
    feats = db.query(Feature).filter(Feature.project_id == project_id).all()
    comps = db.query(ArchitectureComponent).filter(ArchitectureComponent.project_id == project_id).all()
    decs = db.query(Decision).filter(Decision.project_id == project_id).all()
    claims = db.query(EvidenceClaim).filter(EvidenceClaim.project_id == project_id).all()
    issues = db.query(ValidationIssue).filter(ValidationIssue.project_id == project_id).all()

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
    project_id: str,
    requirement_id: str,
    body: EditRequirementRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    ATHENA Living Blueprint: Modifies requirement, calculates downstream affected entities, and revalidates project.
    """
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    analyzer = ImpactAnalyzer(db)
    result = analyzer.analyze_requirement_change(
        project_id=project_id,
        requirement_id=requirement_id,
        new_title=body.title,
        new_desc=body.description
    )

    return result


@router.post("/{project_id}/decisions/{decision_id}/edit")
def edit_tech_decision_and_revalidate(
    project_id: str,
    decision_id: str,
    body: EditTechDecisionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    ATHENA Living Blueprint: Updates technology choice, propagates changes across affected components, and revalidates.
    """
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    analyzer = ImpactAnalyzer(db)
    result = analyzer.analyze_tech_decision_change(
        project_id=project_id,
        decision_id=decision_id,
        new_choice=body.chosen_option
    )

    return result


@router.post("/{project_id}/documents/ingest")
def ingest_document(
    project_id: str,
    body: DocumentIngestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    ATHENA Local RAG: Ingests uploaded research paper or project spec for context retrieval.
    """
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    rag = RAGService(db)
    chunks = rag.ingesting_document(
        project_id=project_id,
        filename=body.filename,
        content=body.content
    )

    return {"status": "success", "chunks_created": len(chunks)}


@router.get("/{project_id}/documents/search")
def search_documents(
    project_id: str,
    query: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    ATHENA Local RAG: Searches ingested project documents for query context.
    """
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    rag = RAGService(db)
    context = rag.search_context(project_id=project_id, query=query)
    return {"query": query, "context": context}
