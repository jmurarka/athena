from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from app.agents.base_agent import BaseAgent

class CanvasNode(BaseModel):
    id: str
    type: str = Field(..., description="Node component block style (e.g. client, api_gateway, auth_service, load_balancer, microservice, database, cache, message_queue, worker)")
    data: Dict[str, Any] = Field(..., description="Metadata dictionary including label, e.g. {'label': 'Postgres'}")
    position: Dict[str, float] = Field(..., description="Flow layout coordinates mapping, e.g. {'x': 100.0, 'y': 150.0}")

class CanvasEdge(BaseModel):
    id: str
    source: str
    target: str
    animated: bool = False
    label: Optional[str] = None

class CanvasSchema(BaseModel):
    nodes: List[CanvasNode]
    edges: List[CanvasEdge]

class SystemDesignOutput(BaseModel):
    hld_markdown: str = Field(..., description="High-Level Design documentation report in markdown format")
    canvas: CanvasSchema = Field(..., description="React Flow node and connection mapping definitions")

SYSTEM_DESIGN_SYSTEM_PROMPT = """You are the Lead Systems Architect. Review the Product Vision and Features: {product_data}.
Generate a comprehensive HLD markdown report AND a structured JSON Graph representing nodes and edges for React Flow.
Supported node types: 'client', 'api_gateway', 'auth_service', 'load_balancer', 'microservice', 'database', 'cache', 'message_queue', 'worker'.
Positions must be mapped logically (e.g. client at x: 100, gateway at x: 300, database at x: 700) to keep the flow clean.
Your response must strictly match the requested JSON schema.
"""

class SystemDesignAgent(BaseAgent):
    """
    System Design Agent generates High-Level Architecture specifications
    and compiles visual systems connection schemas.
    """
    def __init__(self):
        super().__init__(
            system_prompt=SYSTEM_DESIGN_SYSTEM_PROMPT,
            response_model=SystemDesignOutput,
            temperature=0.1
        )
