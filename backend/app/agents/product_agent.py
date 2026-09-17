from typing import List, Optional
from pydantic import BaseModel, Field
from app.agents.base_agent import BaseAgent


class PersonaItem(BaseModel):
    role: str = Field(..., description="Role/title of the persona")
    needs: List[str] = Field(..., description="Core business needs or expectations")
    frustrations: List[str] = Field(..., description="Key frustrations or current pain points")


class RequirementItem(BaseModel):
    code: str = Field(..., description="Requirement identifier code e.g. REQ-001, REQ-002")
    title: str = Field(..., description="Short title of the requirement")
    description: str = Field(..., description="Detailed functional specification")
    category: str = Field(default="functional", description="functional, non_functional, or constraint")
    priority: str = Field(default="high", description="high, medium, low")


class FeatureItem(BaseModel):
    code: str = Field(..., description="Feature identifier code e.g. F-001, F-002")
    title: str = Field(..., description="Name of the feature")
    description: str = Field(..., description="Brief explanation of feature functionality")
    user_story: str = Field(..., description="As a <user>, I want <goal> so that <benefit>")
    is_mvp: bool = Field(default=True, description="Whether included in MVP scope")
    mapped_requirement_codes: List[str] = Field(default_factory=list, description="Requirement codes (REQ-xxx) this feature implements")


class NFRItem(BaseModel):
    category: str = Field(..., description="Category e.g. Performance, Scalability, Security, Offline, Privacy")
    spec: str = Field(..., description="Technical requirement specification")


class ProductOutput(BaseModel):
    vision: str = Field(..., description="Elevator pitch and product vision statement")
    personas: List[PersonaItem] = Field(..., description="Target user profiles")
    requirements: List[RequirementItem] = Field(..., description="List of atomic requirements (REQ-001, REQ-002, etc.)")
    features: List[FeatureItem] = Field(..., description="List of product features (F-001, F-002, etc.) mapped to REQ codes")
    nfrs: List[NFRItem] = Field(..., description="Non-functional requirements catalog")


PRODUCT_SYSTEM_PROMPT = """You are ATHENA's Product Agent. Analyze the problem statement: {problem_statement}.
Domain Focus: {domain}
Focus Areas: {focus_areas}

Generate:
1. Product Vision statement
2. Target User Personas
3. Structured Requirement list (REQ-001, REQ-002, REQ-003...). Include functional, non-functional, and constraint requirements.
4. Product Features list (F-001, F-002...) with user stories, MVP flags, and explicit mapping to requirement codes (`mapped_requirement_codes`).
5. Non-Functional Requirements (Performance, Security, Local Privacy, Scalability).

Return output strictly matching the JSON schema.
"""


class ProductAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            system_prompt=PRODUCT_SYSTEM_PROMPT,
            response_model=ProductOutput,
            temperature=0.2
        )
