from pydantic import BaseModel, Field, model_validator
from typing import List, Any, Dict
from app.agents.base_agent import BaseAgent

class RoadmapPhase(BaseModel):
    phase_name: str = Field(default="Milestone Phase", description="Name of the milestone phase")
    duration: str = Field(default="2-4 Weeks", description="Estimated duration (e.g. Weeks 1-4)")
    deliverables: List[str] = Field(default_factory=list, description="Key deliverables under this phase")

    @model_validator(mode='before')
    @classmethod
    def pre_validate(cls, data: Any) -> Any:
        if isinstance(data, str):
            return {
                "phase_name": data,
                "duration": "2-4 Weeks",
                "deliverables": [f"Deliver core objectives for {data}"]
            }
        if isinstance(data, dict):
            deliv = data.get("deliverables") or []
            if isinstance(deliv, str):
                deliv = [deliv]
            return {
                "phase_name": data.get("phase_name") or data.get("name") or "Milestone Phase",
                "duration": data.get("duration") or "2-4 Weeks",
                "deliverables": deliv
            }
        return data

class RoadmapOutput(BaseModel):
    phases: List[RoadmapPhase] = Field(default_factory=list, description="Milestone phases of the development roadmap")
    mvp_scope: List[str] = Field(default_factory=list, description="Features included in the core MVP scope")
    v2_scope: List[str] = Field(default_factory=list, description="Features deferred to future V2 scope")

ROADMAP_SYSTEM_PROMPT = """You are the Agile Program Manager. Review all generated artifacts (Product, Architecture, Feasibility, Market).
Generate an execution roadmap divided into 3 milestones:
- Milestone 1: Core Foundation (MVP)
- Milestone 2: Functional Core
- Milestone 3: Scale & Launch (V2)
Your response must strictly match the requested JSON schema.
"""

class RoadmapAgent(BaseAgent):
    """
    Roadmap Agent compiles execution timelines and MVP boundaries.
    """
    def __init__(self):
        super().__init__(
            system_prompt=ROADMAP_SYSTEM_PROMPT,
            response_model=RoadmapOutput,
            temperature=0.2
        )
