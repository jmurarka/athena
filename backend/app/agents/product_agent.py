from typing import List, Optional
from pydantic import BaseModel, Field
from app.agents.base_agent import BaseAgent


class PersonaItem(BaseModel):
    role: str = Field(default="User", description="Role/title of the persona")
    needs: List[str] = Field(default_factory=list, description="Core business needs or expectations")
    frustrations: List[str] = Field(default_factory=list, description="Key frustrations or current pain points")


class RequirementItem(BaseModel):
    code: str = Field(default="REQ-001", description="Requirement identifier code e.g. REQ-001, REQ-002")
    title: str = Field(default="Core Requirement", description="Short title of the requirement")
    description: str = Field(default="Functional specification", description="Detailed functional specification")
    category: str = Field(default="functional", description="functional, non_functional, or constraint")
    priority: str = Field(default="high", description="high, medium, low")


class FeatureItem(BaseModel):
    code: str = Field(default="F-001", description="Feature identifier code e.g. F-001, F-002")
    title: str = Field(default="Core Feature", description="Name of the feature")
    description: str = Field(default="Feature description", description="Brief explanation of feature functionality")
    user_story: str = Field(default="As a user, I want this feature so that I can achieve my goal.", description="As a <user>, I want <goal> so that <benefit>")
    is_mvp: bool = Field(default=True, description="Whether included in MVP scope")
    mapped_requirement_codes: List[str] = Field(default_factory=list, description="Requirement codes (REQ-xxx) this feature implements")


class NFRItem(BaseModel):
    category: str = Field(default="Performance", description="Category e.g. Performance, Scalability, Security, Offline, Privacy")
    spec: str = Field(default="Low latency operation", description="Technical requirement specification")


class ProductOutput(BaseModel):
    vision: str = Field(default="Structured system for user requirements.", description="Elevator pitch and product vision statement")
    personas: List[PersonaItem] = Field(default_factory=list, description="Target user profiles")
    requirements: List[RequirementItem] = Field(default_factory=list, description="List of atomic requirements (REQ-001, REQ-002, etc.)")
    features: List[FeatureItem] = Field(default_factory=list, description="List of product features (F-001, F-002, etc.) mapped to REQ codes")
    nfrs: List[NFRItem] = Field(default_factory=list, description="Non-functional requirements catalog")


PRODUCT_SYSTEM_PROMPT = """You are ATHENA's Product Agent. Analyze the problem statement: {problem_statement}.
Domain Focus: {domain}
Focus Areas: {focus_areas}

You must output a concrete JSON object with real data, NOT a schema or type description.
Example format:
{{
  "vision": "A trustworthy AI system detecting fake news and evaluating source credibility.",
  "personas": [{{"role": "News Reader", "needs": ["Fact-checked news"], "frustrations": ["Misleading clickbait"]}}],
  "requirements": [{{"code": "REQ-001", "title": "Article Ingestion", "description": "Ingests article text and URLs", "category": "functional", "priority": "high"}}],
  "features": [{{"code": "F-001", "title": "Credibility Scorer", "description": "Analyzes claims and assigns credibility score", "user_story": "As a reader, I want credibility scores so that I know what to trust", "is_mvp": true, "mapped_requirement_codes": ["REQ-001"]}}],
  "nfrs": [{{"category": "Performance", "spec": "API response time under 500ms"}}]
}}

Output valid JSON strictly matching the example format above.
"""


class ProductAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            system_prompt=PRODUCT_SYSTEM_PROMPT,
            response_model=ProductOutput,
            temperature=0.2
        )
