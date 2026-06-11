from pydantic import BaseModel, Field
from typing import List
from app.agents.base_agent import BaseAgent

class PersonaItem(BaseModel):
    role: str = Field(..., description="Role/title of the persona")
    needs: List[str] = Field(..., description="Core business needs or expectations")
    frustrations: List[str] = Field(..., description="Key frustrations or current pain points")

class FeatureItem(BaseModel):
    name: str = Field(..., description="Name of the feature")
    desc: str = Field(..., description="Brief explanation of the feature functionality")

class FeatureEpic(BaseModel):
    epic: str = Field(..., description="Functional group or Epic title")
    items: List[FeatureItem] = Field(..., description="List of core features under this epic group")

class NFRItem(BaseModel):
    category: str = Field(..., description="Category (e.g. Performance, Scalability, Security, Compliance)")
    spec: str = Field(..., description="Technical requirement specification")

class ProductOutput(BaseModel):
    vision: str = Field(..., description="Elevator pitch and product vision statement")
    personas: List[PersonaItem] = Field(..., description="Target user profiles")
    features: List[FeatureEpic] = Field(..., description="Core features catalog grouped by functional epics")
    nfrs: List[NFRItem] = Field(..., description="Non-functional requirements catalog")

PRODUCT_SYSTEM_PROMPT = """You are the Principal Product Owner. Analyze the problem statement: {problem_statement}.
Using the supervisor's guidelines:
Domain: {domain}
Scale: {complexity_scale}
Focus Areas: {focus_areas}

Generate:
- Product Vision statement
- Target User Personas (minimum 2)
- Feature List grouped by Epic (Functional Blocks)
- Non-Functional Requirements (Performance, Scale, Security)
Your response must strictly match the requested JSON schema.
"""

class ProductAgent(BaseAgent):
    """
    Product Agent generates the core product requirement definitions.
    """
    def __init__(self):
        super().__init__(
            system_prompt=PRODUCT_SYSTEM_PROMPT,
            response_model=ProductOutput,
            temperature=0.2
        )
