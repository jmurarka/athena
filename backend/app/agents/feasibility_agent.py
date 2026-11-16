from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, model_validator
from app.agents.base_agent import BaseAgent


class RiskItem(BaseModel):
    risk: str = Field(default="Technical implementation complexity", description="Description of technical risk")
    severity: str = Field(default="Medium", description="High, Medium, Low")
    mitigation: str = Field(default="Adopt modular architecture and incremental automated testing", description="Suggested mitigation strategy")

    @model_validator(mode='before')
    @classmethod
    def pre_validate(cls, data: Any) -> Any:
        if isinstance(data, str):
            return {
                "risk": data,
                "severity": "Medium",
                "mitigation": "Mitigate via phased delivery and testing"
            }
        if isinstance(data, dict):
            return {
                "risk": data.get("risk") or data.get("title") or data.get("name") or "Technical risk",
                "severity": data.get("severity") or data.get("impact") or "Medium",
                "mitigation": data.get("mitigation") or data.get("action") or "Continuous monitoring"
            }
        return data


class BuildabilityStatus(BaseModel):
    technical_feasibility: str = Field(default="pass", description="status: pass, warning, blocker")
    data_availability: str = Field(default="pass", description="status: pass, warning, blocker")
    required_skills: str = Field(default="pass", description="status: pass, warning, blocker")
    infrastructure: str = Field(default="pass", description="status: pass, warning, blocker")
    timeline: str = Field(default="pass", description="status: pass, warning, blocker")
    blockers: List[str] = Field(default_factory=list, description="Immediate buildability blockers")

    @model_validator(mode='before')
    @classmethod
    def pre_validate(cls, data: Any) -> Any:
        if isinstance(data, dict):
            clean = {}
            for k in ["technical_feasibility", "data_availability", "required_skills", "infrastructure", "timeline"]:
                clean[k] = data.get(k) or "pass"
            clean["blockers"] = data.get("blockers") or []
            return clean
        return {"technical_feasibility": "pass", "data_availability": "pass", "required_skills": "pass", "infrastructure": "pass", "timeline": "pass", "blockers": []}


class FeasibilityOutput(BaseModel):
    buildability: BuildabilityStatus = Field(default_factory=BuildabilityStatus, description="Evaluation of practical buildability")
    risks: List[RiskItem] = Field(default_factory=list, description="Technical implementation risks and mitigations")
    resource_requirements: List[str] = Field(default_factory=list, description="Required skill profiles and infrastructure")
    feasibility_summary: str = Field(default="Feasibility evaluation completed.", description="Overall feasibility analysis report")

    @model_validator(mode='before')
    @classmethod
    def pre_validate(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "feasibility_summary" not in data:
                data["feasibility_summary"] = data.get("summary") or "Technical feasibility evaluation completed."
            if "buildability" not in data or not isinstance(data.get("buildability"), dict):
                data["buildability"] = {}
        return data


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
