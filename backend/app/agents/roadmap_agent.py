from pydantic import BaseModel, Field
from typing import List
from app.agents.base_agent import BaseAgent

class RoadmapPhase(BaseModel):
    phase_name: str = Field(..., description="Name of the milestone phase")
    duration: str = Field(..., description="Estimated duration (e.g. Weeks 1-4)")
    deliverables: List[str] = Field(..., description="Key deliverables under this phase")

class RoadmapOutput(BaseModel):
    phases: List[RoadmapPhase] = Field(..., description="Milestone phases of the development roadmap")
    mvp_scope: List[str] = Field(..., description="Features included in the core MVP scope")
    v2_scope: List[str] = Field(..., description="Features deferred to future V2 scope")

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
