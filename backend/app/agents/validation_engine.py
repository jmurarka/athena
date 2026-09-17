from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.agents.base_agent import BaseAgent


class ValidationIssueItem(BaseModel):
    severity: str = Field(..., description="critical, warning, or review")
    code: str = Field(..., description="Issue code e.g. VAL-MISSING-AUTH, VAL-UNMAPPED-REQ")
    title: str = Field(..., description="Short title of the detected flaw")
    description: str = Field(..., description="Detailed description of the requirement or architecture contradiction")
    suggested_fix: str = Field(..., description="Actionable proposed correction")
    affected_entities: List[str] = Field(default_factory=list, description="IDs/codes of affected REQ, F, or Component entities")


class ValidationMetrics(BaseModel):
    total_requirements: int = Field(default=0)
    mapped_requirements: int = Field(default=0)
    coverage_score: float = Field(default=0.0, description="Requirement coverage fraction (0.0 to 1.0)")
    contradiction_rate: float = Field(default=0.0, description="Fraction of decisions/architecture with contradictions")
    unsupported_claim_rate: float = Field(default=0.0, description="Fraction of claims that are unverified")
    critical_count: int = Field(default=0)
    warning_count: int = Field(default=0)
    review_count: int = Field(default=0)


class ValidationOutput(BaseModel):
    metrics: ValidationMetrics = Field(..., description="Calculated project health and coverage metrics")
    issues: List[ValidationIssueItem] = Field(..., description="Identified critical, warning, and review issues ('Break My Plan')")
    recommended_next_steps: List[str] = Field(..., description="Ordered list of recommended steps to fix validation issues")


VALIDATION_SYSTEM_PROMPT = """You are ATHENA's Project Validation Engine ("Break My Plan").
Your goal is to aggressively challenge the generated project plan and discover hidden flaws, missing services, contradictions, unverified claims, and scale mismatches.

Review:
- Requirements: {requirements_data}
- Features: {features_data}
- Architecture Components: {components_data}
- Decisions: {decisions_data}
- Evidence Claims: {claims_data}
- Feasibility Risks: {feasibility_data}

Rules to enforce:
1. CRITICAL: Identify requirements that have NO feature or component implementing them.
2. CRITICAL: Identify missing security/authentication services if user auth or user data is required.
3. WARNING: Detect scale or constraint contradictions (e.g. offline requirement vs cloud API choice, low budget vs massive infra).
4. WARNING: Flag unverified or unsupported market/technical claims.
5. REVIEW: Flag technology choices that lack supporting performance or business requirements.

Calculate:
- Requirement Coverage: mapped_requirements / total_requirements
- Contradiction Rate: contradictory_decisions / total_decisions
- Unsupported Claim Rate: unverified_claims / total_claims

Return output strictly matching the JSON schema.
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
