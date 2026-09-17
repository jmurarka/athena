from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.agents.base_agent import BaseAgent


class CanvasNode(BaseModel):
    id: str
    type: str = Field(..., description="Node component type e.g. client, api_gateway, auth_service, microservice, database, cache, worker")
    data: Dict[str, Any] = Field(..., description="Metadata dict e.g. {'label': 'PostgreSQL'}")
    position: Dict[str, float] = Field(..., description="Coordinates mapping e.g. {'x': 100.0, 'y': 150.0}")


class CanvasEdge(BaseModel):
    id: str
    source: str
    target: str
    animated: bool = False
    label: Optional[str] = None


class CanvasSchema(BaseModel):
    nodes: List[CanvasNode]
    edges: List[CanvasEdge]


class DecisionItem(BaseModel):
    topic: str = Field(..., description="Technology decision topic e.g. Database Selection, Auth Mechanism")
    chosen_option: str = Field(..., description="Selected technology or approach")
    why_chosen: str = Field(..., description="Core architectural justification")
    why_not_alternatives: str = Field(..., description="Why alternative solutions were rejected")
    trade_offs: str = Field(..., description="Disadvantages and trade-offs of this choice")
    assumptions: str = Field(..., description="Assumptions made during decision")


class ComponentItem(BaseModel):
    component_id_name: str = Field(..., description="Machine identifier e.g. auth_service, postgres_db")
    name: str = Field(..., description="Human readable name e.g. Authentication Service")
    component_type: str = Field(..., description="api_gateway, database, worker, auth_service, frontend, cache")
    tech_stack: str = Field(..., description="Selected tech stack e.g. PostgreSQL, Redis, FastAPI")
    description: str = Field(..., description="Purpose and functionality of component")
    mapped_feature_codes: List[str] = Field(default_factory=list, description="Feature codes (F-xxx) implemented by this component")


class SystemDesignOutput(BaseModel):
    hld_markdown: str = Field(..., description="High-Level Design documentation report in markdown format")
    components: List[ComponentItem] = Field(..., description="List of architecture components mapped to feature codes")
    decisions: List[DecisionItem] = Field(..., description="List of explicit technology decision explanations with trade-offs")
    canvas: CanvasSchema = Field(..., description="React Flow node and edge definitions")


SYSTEM_DESIGN_SYSTEM_PROMPT = """You are ATHENA's Lead System Architect.
Review Product Vision & Features: {product_data}.

Generate:
1. High-Level Design (HLD) documentation report.
2. Architecture Components list (e.g. API Gateway, Auth Service, Postgres DB) with mapped feature codes (F-xxx).
3. Technology Decisions with explicit 'Why Chosen', 'Why Not Alternatives', 'Trade-offs', and 'Assumptions'.
4. React Flow Canvas Node/Edge graph layout schema.

Positions must be mapped cleanly in a top-left to right DAG flow (e.g. Client x:100, Gateway x:300, Services x:550, Databases x:800).
Return output strictly matching the JSON schema.
"""


class SystemDesignAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            system_prompt=SYSTEM_DESIGN_SYSTEM_PROMPT,
            response_model=SystemDesignOutput,
            temperature=0.1
        )
