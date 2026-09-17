from typing import List, Optional
from pydantic import BaseModel, Field
from app.agents.base_agent import BaseAgent


class RiskItem(BaseModel):
    risk: str = Field(..., description="Description of technical risk")
    severity: str = Field(..., description="High, Medium, Low")
    mitigation: str = Field(..., description="Suggested mitigation strategy")


class BuildabilityStatus(BaseModel):
    technical_feasibility: str = Field(description="status: pass, warning, blocker")
    data_availability: str = Field(description="status: pass, warning, blocker")
    required_skills: str = Field(description="status: pass, warning, blocker")
    infrastructure: str = Field(description="status: pass, warning, blocker")
    timeline: str = Field(description="status: pass, warning, blocker")
    blockers: List[str] = Field(default_factory=list, description="Immediate buildability blockers")


class FeasibilityOutput(BaseModel):
    buildability: BuildabilityStatus = Field(..., description="Evaluation of practical buildability")
    risks: List[RiskItem] = Field(..., description="Technical implementation risks and mitigations")
    resource_requirements: List[str] = Field(..., description="Required skill profiles and infrastructure")
    feasibility_summary: str = Field(..., description="Overall feasibility analysis report")


FEASIBILITY_SYSTEM_PROMPT = """You are ATHENA's Feasibility Analysis Agent.
Analyze the product spec: {product_data}, architecture: {architecture_data}, and research: {research_data}.

Evaluate:
1. Technical buildability (Pass / Warning / Blocker for technical feasibility, data availability, skills, infrastructure, timeline).
2. Explicit blockers (e.g. unavailable dataset, unrealistic budget, specialized ML required).
3. Risk matrix (Severity + Mitigations).
4. Required team skills & hardware/cloud resources.

Return output strictly matching the JSON schema.
"""


class FeasibilityAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            system_prompt=FEASIBILITY_SYSTEM_PROMPT,
            response_model=FeasibilityOutput,
            temperature=0.2
        )
