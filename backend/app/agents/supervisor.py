from pydantic import BaseModel, Field
from typing import List
from app.agents.base_agent import BaseAgent

class SupervisorOutput(BaseModel):
    domain: str = Field(..., description="Target industry domain or vertical")
    complexity_scale: str = Field(..., description="Estimated scale of the system (e.g. Small business SaaS, High-throughput microservice mesh)")
    focus_areas: List[str] = Field(..., description="Crucial architectural or product focus points downstream agents must resolve")
    technical_constraints: List[str] = Field(..., description="Assumed baseline technological constraints or guidelines")

SUPERVISOR_SYSTEM_PROMPT = """You are the Lead Architect Supervisor.
Your job is to analyze the raw problem statement: {problem_statement}
Decompose this statement into key dimensions (Primary Goal, Target Domain, Complexity Scale).
Output a structured execution plan outlining the tone and technical assumptions for downstream agents.
Provide clean, concise JSON output matching the requested schema.
"""

class SupervisorAgent(BaseAgent):
    """
    Supervisor Agent analyzes the raw user problem statement
    and creates a structural decomposition plan.
    """
    def __init__(self):
        super().__init__(
            system_prompt=SUPERVISOR_SYSTEM_PROMPT,
            response_model=SupervisorOutput,
            temperature=0.1
        )
