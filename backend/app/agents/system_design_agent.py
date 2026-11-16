from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, model_validator
from app.agents.base_agent import BaseAgent


class CanvasNode(BaseModel):
    id: str = "node_1"
    type: str = Field(default="customShape", description="Node component type")
    data: Dict[str, Any] = Field(default_factory=dict, description="Metadata dict")
    position: Dict[str, float] = Field(default_factory=lambda: {"x": 100.0, "y": 100.0}, description="Coordinates mapping")

    @model_validator(mode='before')
    @classmethod
    def pre_validate(cls, data: Any) -> Any:
        if isinstance(data, dict):
            nid = str(data.get("id") or data.get("name") or "node_1")
            
            # Safe position conversion
            pos = data.get("position")
            valid_pos = {"x": 100.0, "y": 100.0}
            if isinstance(pos, dict):
                try:
                    valid_pos = {
                        "x": float(pos.get("x", 100.0)),
                        "y": float(pos.get("y", 100.0))
                    }
                except Exception:
                    valid_pos = {"x": 100.0, "y": 100.0}
            elif isinstance(pos, (int, float, str)):
                try:
                    num = float(pos)
                    valid_pos = {"x": num, "y": 100.0}
                except Exception:
                    valid_pos = {"x": 100.0, "y": 100.0}

            # Safe data label conversion
            ndata = data.get("data")
            if not isinstance(ndata, dict):
                label = data.get("name") or data.get("label") or nid
                ndata = {"label": str(label)}
            elif "label" not in ndata:
                ndata["label"] = str(data.get("name") or data.get("title") or nid)

            return {
                "id": nid,
                "type": str(data.get("type") or "customShape"),
                "data": ndata,
                "position": valid_pos
            }
        return data


class CanvasEdge(BaseModel):
    id: str = "edge_1"
    source: str = "node_1"
    target: str = "node_2"
    animated: bool = True
    label: Optional[str] = None

    @model_validator(mode='before')
    @classmethod
    def pre_validate(cls, data: Any) -> Any:
        if isinstance(data, dict):
            src = str(data.get("source") or "node_1")
            tgt = str(data.get("target") or "node_2")
            eid = str(data.get("id") or f"e_{src}_{tgt}")
            lbl = data.get("label")
            return {
                "id": eid,
                "source": src,
                "target": tgt,
                "animated": bool(data.get("animated", True)),
                "label": str(lbl) if lbl is not None else None
            }
        return data


class CanvasSchema(BaseModel):
    nodes: List[CanvasNode] = Field(default_factory=list)
    edges: List[CanvasEdge] = Field(default_factory=list)


class DecisionItem(BaseModel):
    topic: str = Field(default="Architecture Decision", description="Technology decision topic")
    chosen_option: str = Field(default="Standard Stack", description="Selected technology or approach")
    why_chosen: str = Field(default="Proven efficiency and scalability", description="Core architectural justification")
    why_not_alternatives: str = Field(default="Higher complexity or resource requirements", description="Why alternative solutions were rejected")
    trade_offs: str = Field(default="Standard trade-offs associated with selected pattern", description="Disadvantages and trade-offs of this choice")
    assumptions: str = Field(default="Compatible with local execution and deployment constraints", description="Assumptions made during decision")

    @model_validator(mode='before')
    @classmethod
    def pre_validate(cls, data: Any) -> Any:
        if isinstance(data, dict):
            return {
                "topic": data.get("topic") or data.get("title") or "Architecture Decision",
                "chosen_option": data.get("chosen_option") or data.get("choice") or data.get("technology") or "Standard Choice",
                "why_chosen": data.get("why_chosen") or data.get("reason") or "Architectural efficiency and maintainability",
                "why_not_alternatives": data.get("why_not_alternatives") or "High operational overhead or latency",
                "trade_offs": data.get("trade_offs") or "Standard maintenance footprint",
                "assumptions": data.get("assumptions") or "Compatible with project specifications"
            }
        return data


class ComponentItem(BaseModel):
    component_id_name: str = Field(default="service", description="Machine identifier")
    name: str = Field(default="Component Service", description="Human readable name")
    component_type: str = Field(default="service", description="Component type")
    tech_stack: str = Field(default="Standard", description="Selected tech stack")
    description: str = Field(default="", description="Purpose and functionality of component")
    mapped_feature_codes: List[str] = Field(default_factory=list, description="Feature codes")

    @model_validator(mode='before')
    @classmethod
    def pre_validate(cls, data: Any) -> Any:
        if isinstance(data, str):
            return {
                "component_id_name": data.lower().replace(" ", "_"),
                "name": data,
                "component_type": "service",
                "tech_stack": "Standard",
                "description": f"Component responsible for {data}",
                "mapped_feature_codes": []
            }
        if isinstance(data, dict):
            name = data.get("name") or data.get("title") or "Component Service"
            c_id = data.get("component_id_name") or data.get("id") or name.lower().replace(" ", "_")
            return {
                "component_id_name": c_id,
                "name": name,
                "component_type": data.get("component_type") or data.get("type") or "service",
                "tech_stack": data.get("tech_stack") or data.get("tech") or "Standard",
                "description": data.get("description") or "",
                "mapped_feature_codes": data.get("mapped_feature_codes") or []
            }
        return data


class SystemDesignOutput(BaseModel):
    hld_markdown: str = Field(default="High-Level Design documentation report.", description="High-Level Design documentation report")
    components: List[ComponentItem] = Field(default_factory=list, description="List of architecture components")
    decisions: List[DecisionItem] = Field(default_factory=list, description="List of explicit technology decision explanations")
    canvas: CanvasSchema = Field(default_factory=CanvasSchema, description="React Flow node and edge definitions")

    @model_validator(mode='before')
    @classmethod
    def pre_validate(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "hld_markdown" not in data:
                data["hld_markdown"] = data.get("summary") or data.get("architecture_summary") or "High-Level Architecture Design"
            
            canvas = data.get("canvas")
            if not isinstance(canvas, dict):
                canvas = {"nodes": [], "edges": []}
            
            # If nodes list is empty, generate layout from components
            comps = data.get("components") or []
            nodes = canvas.get("nodes") or []
            if not nodes and comps:
                x_coord = 100.0
                gen_nodes = []
                gen_edges = []
                prev_id = None
                for i, c in enumerate(comps):
                    c_id = c.get("component_id_name") if isinstance(c, dict) else f"comp_{i}"
                    c_name = c.get("name") if isinstance(c, dict) else str(c)
                    c_type = c.get("component_type") if isinstance(c, dict) else "service"
                    gen_nodes.append({
                        "id": str(c_id),
                        "type": "customShape",
                        "data": {"label": str(c_name), "shape": "db" if "db" in str(c_type).lower() or "data" in str(c_type).lower() else "rect"},
                        "position": {"x": x_coord, "y": 150.0}
                    })
                    if prev_id:
                        gen_edges.append({
                            "id": f"e_{prev_id}_{c_id}",
                            "source": prev_id,
                            "target": str(c_id),
                            "animated": True
                        })
                    prev_id = str(c_id)
                    x_coord += 200.0
                canvas["nodes"] = gen_nodes
                canvas["edges"] = gen_edges
            data["canvas"] = canvas
        return data


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
