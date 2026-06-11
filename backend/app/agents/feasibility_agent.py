from pydantic import BaseModel, Field
from typing import List
from app.agents.base_agent import BaseAgent

class RiskItem(BaseModel):
    risk: str = Field(..., description="Description of the risk")
    impact: str = Field(..., description="Estimated impact level (e.g. High, Medium, Low)")
    mitigation: str = Field(..., description="Suggested risk mitigation strategy")

class FeasibilityOutput(BaseModel):
    risks: List[RiskItem] = Field(..., description="Identified technical implementation risks and mitigations")
    resource_requirements: List[str] = Field(..., description="Team skill profiles and technical resource requirements")
    technical_feasibility_summary: str = Field(..., description="Executive summary of the technical feasibility")

FEASIBILITY_SYSTEM_PROMPT = """You are the Feasibility Director. Analyze product specifications, competitor landscape, and systems architecture.
Assess:
- Technical implementation risks (High, Medium, Low)
- Resource skill bottlenecks
- MVP development constraints
Your response must strictly match the requested JSON schema.
"""

class FeasibilityAgent(BaseAgent):
    """
    Feasibility Agent estimates delivery risks and resource skill barriers.
    """
    def __init__(self):
        super().__init__(
            system_prompt=FEASIBILITY_SYSTEM_PROMPT,
            response_model=FeasibilityOutput,
            temperature=0.2
        )
