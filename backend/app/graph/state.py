from typing import TypedDict, Optional, Dict, Any, List


class GraphState(TypedDict):
    """
    Defines the shared state dictionary passed between agent nodes
    in ATHENA's LangGraph orchestration workflow.
    """
    project_id: str
    problem_statement: str
    
    # Execution states
    execution_plan: Optional[str]
    
    # Generated deliverables & graph data
    problem_analysis_data: Optional[Dict[str, Any]]
    product_data: Optional[Dict[str, Any]]
    research_data: Optional[Dict[str, Any]]
    system_design_data: Optional[Dict[str, Any]]
    system_design_canvas: Optional[Dict[str, Any]]
    feasibility_data: Optional[Dict[str, Any]]
    roadmap_data: Optional[Dict[str, Any]]
    validation_data: Optional[Dict[str, Any]]
    
    # Metadata tracking
    token_usage: Dict[str, int]
    latency_ms: Dict[str, int]
