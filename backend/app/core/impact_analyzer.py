import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.graph_models import Requirement, Feature, ArchitectureComponent, Decision, ValidationIssue
from app.models.project import Project
from app.agents.validation_engine import ValidationEngine

logger = logging.getLogger(__name__)


class ImpactAnalyzer:
    """
    ATHENA Living Blueprint Engine:
    Detects affected entities when a user modifies a requirement, feature, or technology choice,
    identifies downstream dependencies, and re-triggers validation.
    """
    def __init__(self, db: Session):
        self.db = db

    def analyze_requirement_change(self, project_id: str, requirement_id: str, new_title: str, new_desc: str) -> Dict[str, Any]:
        """
        Analyzes impact when a user edits or deletes a requirement.
        """
        req = self.db.query(Requirement).filter(
            Requirement.id == requirement_id,
            Requirement.project_id == project_id
        ).first()

        if not req:
            return {"error": "Requirement not found"}

        req.title = new_title
        req.description = new_desc
        self.db.commit()

        # Find connected features
        affected_features = []
        for feat_map in req.features:
            affected_features.append({
                "id": str(feat_map.feature.id),
                "code": feat_map.feature.code,
                "title": feat_map.feature.title
            })

        # Find connected components via features
        affected_components = []
        for feat_map in req.features:
            for comp_map in feat_map.feature.components:
                affected_components.append({
                    "id": str(comp_map.component.id),
                    "name": comp_map.component.name,
                    "tech_stack": comp_map.component.tech_stack
                })

        # Re-run project validation
        revalidation_result = self.revalidate_project(project_id)

        return {
            "requirement_code": req.code,
            "affected_features": affected_features,
            "affected_components": affected_components,
            "revalidation": revalidation_result
        }

    def analyze_tech_decision_change(self, project_id: str, decision_id: str, new_choice: str) -> Dict[str, Any]:
        """
        Analyzes impact when a user changes a technology decision (e.g. MongoDB -> PostgreSQL).
        """
        dec = self.db.query(Decision).filter(
            Decision.id == decision_id,
            Decision.project_id == project_id
        ).first()

        if not dec:
            return {"error": "Decision not found"}

        old_choice = dec.chosen_option
        dec.chosen_option = new_choice
        self.db.commit()

        # Find components using old or affected tech
        affected_components = self.db.query(ArchitectureComponent).filter(
            ArchitectureComponent.project_id == project_id
        ).all()

        updated_components = []
        for comp in affected_components:
            if comp.tech_stack and old_choice.lower() in comp.tech_stack.lower():
                comp.tech_stack = comp.tech_stack.replace(old_choice, new_choice)
                updated_components.append(comp.name)
        
        self.db.commit()

        revalidation_result = self.revalidate_project(project_id)

        return {
            "decision_topic": dec.topic,
            "previous_choice": old_choice,
            "new_choice": new_choice,
            "updated_components": updated_components,
            "revalidation": revalidation_result
        }

    def revalidate_project(self, project_id: str) -> Dict[str, Any]:
        """
        Runs the ValidationEngine against stored graph entities and updates project health metrics.
        """
        reqs = self.db.query(Requirement).filter(Requirement.project_id == project_id).all()
        feats = self.db.query(Feature).filter(Feature.project_id == project_id).all()
        comps = self.db.query(ArchitectureComponent).filter(ArchitectureComponent.project_id == project_id).all()
        decs = self.db.query(Decision).filter(Decision.project_id == project_id).all()

        reqs_data = [{"code": r.code, "title": r.title, "desc": r.description} for r in reqs]
        feats_data = [{"code": f.code, "title": f.title, "is_mvp": f.is_mvp} for f in feats]
        comps_data = [{"name": c.name, "type": c.component_type, "tech": c.tech_stack} for c in comps]
        decs_data = [{"topic": d.topic, "chosen": d.chosen_option} for d in decs]

        engine = ValidationEngine()
        val_output, latency, tokens = engine.validate_plan(
            requirements_data=reqs_data,
            features_data=feats_data,
            components_data=comps_data,
            decisions_data=decs_data,
            claims_data=[],
            feasibility_data={}
        )

        # Update Project health_metrics
        proj = self.db.query(Project).filter(Project.id == project_id).first()
        if proj and hasattr(val_output, 'metrics'):
            proj.health_metrics = {
                "coverage_score": val_output.metrics.coverage_score,
                "contradiction_rate": val_output.metrics.contradiction_rate,
                "unsupported_claim_rate": val_output.metrics.unsupported_claim_rate,
                "critical_count": val_output.metrics.critical_count,
                "warning_count": val_output.metrics.warning_count,
                "review_count": val_output.metrics.review_count,
                "total_requirements": val_output.metrics.total_requirements,
                "mapped_requirements": val_output.metrics.mapped_requirements,
            }

            # Delete old validation issues and save new ones
            self.db.query(ValidationIssue).filter(ValidationIssue.project_id == project_id).delete()
            for issue in val_output.issues:
                v_issue = ValidationIssue(
                    project_id=project_id,
                    severity=issue.severity,
                    code=issue.code,
                    title=issue.title,
                    description=issue.description,
                    suggested_fix=issue.suggested_fix,
                    affected_entities=issue.affected_entities
                )
                self.db.add(v_issue)

            self.db.commit()

        return {
            "status": "success",
            "health_metrics": proj.health_metrics if proj else {}
        }
