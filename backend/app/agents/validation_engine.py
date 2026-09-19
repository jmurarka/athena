from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.agents.base_agent import BaseAgent


class ValidationIssueItem(BaseModel):
    severity: str = Field(default="warning", description="critical, warning, or review")
    code: str = Field(default="VAL-NOTICE", description="Issue code e.g. VAL-MISSING-AUTH, VAL-UNMAPPED-REQ")
    title: str = Field(default="Plan Notice", description="Short title of the detected flaw")
    description: str = Field(default="Potential concern in architecture or requirements.", description="Detailed description of the requirement or architecture contradiction")
    suggested_fix: str = Field(default="Review components.", description="Actionable proposed correction")
    affected_entities: List[str] = Field(default_factory=list, description="IDs/codes of affected REQ, F, or Component entities")


class ValidationMetrics(BaseModel):
    total_requirements: int = Field(default=0)
    mapped_requirements: int = Field(default=0)
    coverage_score: float = Field(default=1.0, description="Requirement coverage fraction (0.0 to 1.0)")
    contradiction_rate: float = Field(default=0.0, description="Fraction of decisions/architecture with contradictions")
    unsupported_claim_rate: float = Field(default=0.0, description="Fraction of claims that are unverified")
    critical_count: int = Field(default=0)
    warning_count: int = Field(default=0)
    review_count: int = Field(default=0)


class ValidationOutput(BaseModel):
    metrics: ValidationMetrics = Field(default_factory=ValidationMetrics, description="Calculated project health and coverage metrics")
    issues: List[ValidationIssueItem] = Field(default_factory=list, description="Identified critical, warning, and review issues ('Break My Plan')")
    recommended_next_steps: List[str] = Field(default_factory=list, description="Ordered list of recommended steps to fix validation issues")


VALIDATION_SYSTEM_PROMPT = """You are ATHENA's Project Validation Engine ("Break My Plan").
Your goal is to aggressively challenge the generated project plan and discover hidden flaws, missing services, contradictions, and scale mismatches.

Plan Data:
- Requirements: {requirements_data}
- Features: {features_data}
- Architecture Components: {components_data}
- Decisions: {decisions_data}
- Evidence Claims: {claims_data}
- Feasibility Risks: {feasibility_data}

You must output a JSON object containing "metrics", "issues", and "recommended_next_steps".
Example format:
{{
  "metrics": {{
    "total_requirements": 3,
    "mapped_requirements": 3,
    "coverage_score": 1.0,
    "contradiction_rate": 0.0,
    "unsupported_claim_rate": 0.0,
    "critical_count": 0,
    "warning_count": 1,
    "review_count": 0
  }},
  "issues": [
    {{
      "severity": "warning",
      "code": "VAL-AUTH-CHECK",
      "title": "Review Authentication Flow",
      "description": "Ensure API requests are authenticated if user state is stored.",
      "suggested_fix": "Add JWT auth check middleware.",
      "affected_entities": ["REQ-001"]
    }}
  ],
  "recommended_next_steps": [
    "Verify authentication layer on API routes.",
    "Perform end-to-end testing with sample inputs."
  ]
}}

Output valid JSON strictly matching the example format above.
"""


class ValidationEngine(BaseAgent):
    def __init__(self):
        super().__init__(
            system_prompt=VALIDATION_SYSTEM_PROMPT,
            response_model=ValidationOutput,
            temperature=0.1
        )

    def validate_plan(
        self,
        requirements_data: Any,
        features_data: Any,
        components_data: Any,
        decisions_data: Any,
        claims_data: Any,
        feasibility_data: Any
    ):
        prompt_vars = {
            "requirements_data": str(requirements_data),
            "features_data": str(features_data),
            "components_data": str(components_data),
            "decisions_data": str(decisions_data),
            "claims_data": str(claims_data),
            "feasibility_data": str(feasibility_data)
        }
        return self.execute(user_content="Run validation check on current project blueprint.", prompt_vars=prompt_vars)
