import unittest
import os
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.agents.problem_analysis_agent import ProblemAnalysisOutput
from app.agents.product_agent import ProductOutput, RequirementItem, FeatureItem
from app.agents.system_design_agent import SystemDesignOutput, CanvasSchema, CanvasNode, CanvasEdge
from app.agents.feasibility_agent import FeasibilityOutput, BuildabilityStatus
from app.agents.roadmap_agent import RoadmapOutput, RoadmapPhase
from app.agents.validation_engine import ValidationOutput, ValidationMetrics

class TestAgentSchemas(unittest.TestCase):
    def test_problem_analysis_schema(self):
        data = {
            "problem_title": "Uber for Pets",
            "problem_summary": "Connecting pet owners with drivers",
            "target_users": ["Pet Owners", "Verified Drivers"],
            "core_objectives": ["Safe pet transit", "Real-time tracking"],
            "assumptions": ["Drivers are vetted"],
            "constraints": ["Local-first operation"],
            "clarification_questions": [
                {"question": "What pet sizes are allowed?", "rationale": "Vehicle size constraints"}
            ]
        }
        output = ProblemAnalysisOutput.model_validate(data)
        self.assertEqual(output.problem_title, "Uber for Pets")
        self.assertEqual(len(output.target_users), 2)

    def test_product_schema(self):
        data = {
            "vision": "World-class pet transit",
            "personas": [{"role": "Pet Owner", "needs": ["Safe transit"], "frustrations": ["Unsafe taxis"]}],
            "requirements": [
                {"code": "REQ-001", "title": "Pet Booking", "description": "Book a ride with pet info", "category": "functional", "priority": "high"}
            ],
            "features": [
                {"code": "FEAT-001", "title": "Instant Booking", "description": "1-tap booking", "is_mvp": True, "mapped_requirement_codes": ["REQ-001"]}
            ],
            "nfrs": [{"category": "Performance", "spec": "Latency < 200ms"}]
        }
        output = ProductOutput.model_validate(data)
        self.assertEqual(output.vision, "World-class pet transit")
        self.assertEqual(len(output.requirements), 1)

    def test_system_design_schema(self):
        data = {
            "hld_markdown": "# High-Level Architecture\nFastAPI + Postgres",
            "components": [
                {"component_id_name": "api_gateway", "name": "API Gateway", "component_type": "api_gateway", "tech_stack": "FastAPI", "description": "Entry point"}
            ],
            "decisions": [
                {"topic": "Database", "chosen_option": "PostgreSQL", "why_chosen": "ACID compliance"}
            ],
            "canvas": {
                "nodes": [
                    {"id": "gateway", "type": "api_gateway", "data": {"label": "API Gateway"}, "position": {"x": 200.0, "y": 100.0}}
                ],
                "edges": []
            }
        }
        output = SystemDesignOutput.model_validate(data)
        self.assertEqual(len(output.canvas.nodes), 1)
        self.assertEqual(output.canvas.nodes[0].id, "gateway")

    def test_feasibility_schema(self):
        data = {
            "buildability": {
                "technical_feasibility": "pass",
                "data_availability": "pass",
                "required_skills": "pass",
                "infrastructure": "pass",
                "timeline": "pass",
                "blockers": []
            },
            "risks": [
                {"risk": "Driver shortage", "severity": "Medium", "mitigation": "Incentive scheme"}
            ],
            "resource_requirements": ["FastAPI Developer", "React Developer"],
            "feasibility_summary": "Highly feasible project"
        }
        output = FeasibilityOutput.model_validate(data)
        self.assertEqual(output.buildability.technical_feasibility, "pass")

    def test_roadmap_schema(self):
        data = {
            "phases": [
                {"phase_name": "Phase 1: MVP Core", "duration": "4 weeks", "deliverables": ["Auth", "Booking API", "Canvas UI"]}
            ],
            "mvp_scope": ["Pet Booking", "Driver Matching"],
            "v2_scope": ["Live Camera In-Ride Feed"]
        }
        output = RoadmapOutput.model_validate(data)
        self.assertEqual(len(output.phases), 1)
        self.assertEqual(len(output.mvp_scope), 2)

    def test_validation_engine_schema(self):
        data = {
            "metrics": {
                "coverage_score": 0.95,
                "contradiction_rate": 0.0,
                "unsupported_claim_rate": 0.0,
                "critical_count": 0,
                "warning_count": 1,
                "review_count": 0,
                "total_requirements": 5,
                "mapped_requirements": 5
            },
            "issues": [
                {
                    "severity": "warning",
                    "code": "WARN-001",
                    "title": "High traffic risk",
                    "description": "Peak hour rush may delay driver matching",
                    "suggested_fix": "Introduce scheduled rides"
                }
            ],
            "recommended_next_steps": ["Proceed to MVP delivery phase"]
        }
        output = ValidationOutput.model_validate(data)
        self.assertEqual(output.metrics.coverage_score, 0.95)
        self.assertEqual(len(output.issues), 1)

if __name__ == "__main__":
    unittest.main()
