from typing import List, Optional
from pydantic import BaseModel, Field
from app.agents.base_agent import BaseAgent


class CompetitorItem(BaseModel):
    name: str = Field(description="Competitor product or existing approach name")
    strengths: List[str] = Field(description="Key strengths")
    weaknesses: List[str] = Field(description="Key limitations or gaps")
    athena_differentiation: str = Field(description="How our proposed solution differentiates")


class EvidenceClaimItem(BaseModel):
    claim_text: str = Field(description="Factual claim regarding technology performance, market gap, or feasibility")
    source_name: str = Field(description="Reference source name or document standard")
    source_url: Optional[str] = Field(default=None, description="URL or benchmark reference if available")
    verification_status: str = Field(default="verified", description="verified, unverified, or contradicted")
    rationale: str = Field(description="Reasoning behind claim verification")


class ResearchOutput(BaseModel):
    market_overview: str = Field(description="High-level analysis of market context and existing tools")
    competitors: List[CompetitorItem] = Field(description="Competitors and market gap breakdown")
    differentiation_strategy: str = Field(description="Core unique value proposition")
    evidence_claims: List[EvidenceClaimItem] = Field(description="Grounding factual claims with source evidence and verification status")


RESEARCH_SYSTEM_PROMPT = """You are ATHENA's Evidence-Aware Research Agent.
Analyze the problem statement: {problem_statement}.

Conduct a technical and market research analysis:
1. Identify existing solutions and competitors.
2. Outline key strengths, weaknesses, and differentiation parameters.
3. Formulate evidence-backed claims (e.g. "Ollama enables zero cloud egress cost for local inference").
4. Assign verification status (`verified`, `unverified`, or `contradicted`) and site evidence sources for each claim.

Output strictly in valid JSON matching the requested schema.
"""


class ResearchAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            system_prompt=RESEARCH_SYSTEM_PROMPT,
            response_model=ResearchOutput,
            temperature=0.2
        )
