from pydantic import BaseModel, Field
from typing import List
from app.agents.base_agent import BaseAgent

class CompetitorProfile(BaseModel):
    name: str = Field(..., description="Name of the competitor")
    strengths: List[str] = Field(..., description="Competitor's core strengths")
    weaknesses: List[str] = Field(..., description="Competitor's weaknesses or gaps")

class MarketOutput(BaseModel):
    competitors: List[CompetitorProfile] = Field(..., description="List of key competitors in this space")
    gaps: List[str] = Field(..., description="Identified feature or service gaps in the current market")
    differentiation: str = Field(..., description="Value proposition and competitive differentiation strategy")

MARKET_SYSTEM_PROMPT = """You are the Lead Market Researcher. Analyze the problem statement: {problem_statement}.
Identify key competitors (based on internal knowledge + web searches if enabled).
List features, gaps, and recommend a differentiation matrix.
Your response must strictly match the requested JSON schema.
"""

class MarketAgent(BaseAgent):
    """
    Market Agent analyzes competitor matrices and identifies market gaps.
    """
    def __init__(self):
        super().__init__(
            system_prompt=MARKET_SYSTEM_PROMPT,
            response_model=MarketOutput,
            temperature=0.2
        )
