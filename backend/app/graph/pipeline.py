import time
import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, END

from app.core.db import SessionLocal
from app.models.project import Project, ProjectStatus
from app.models.page import Page, AgentType
from app.models.canvas import CanvasState
from app.models.agent_run import AgentRun, AgentRunStatus
from app.graph.state import GraphState

# Import specialized agents
from app.agents.supervisor import SupervisorAgent
from app.agents.product_agent import ProductAgent
from app.agents.system_design_agent import SystemDesignAgent
from app.agents.market_agent import MarketAgent
from app.agents.feasibility_agent import FeasibilityAgent
from app.agents.roadmap_agent import RoadmapAgent

logger = logging.getLogger(__name__)

# Node: Supervisor
def run_supervisor(state: GraphState) -> GraphState:
    logger.info("Executing Supervisor Node...")
    project_id = state["project_id"]
    problem_statement = state["problem_statement"]
    
    db = SessionLocal()
    agent_run = None
    try:
        # Update project status to processing in DB
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.status = ProjectStatus.PROCESSING
            db.commit()
            
        # Log AgentRun start
        agent_run = AgentRun(
            project_id=project_id,
            agent_type=AgentType.PRODUCT,  # mapped to product/supervisor telemetry
            status=AgentRunStatus.STARTED
        )
        db.add(agent_run)
        db.commit()
        db.refresh(agent_run)
        
        # Execute LLM Supervisor Agent
        supervisor = SupervisorAgent()
        output, latency_ms, tokens = supervisor.execute(
            user_content=problem_statement,
            prompt_vars={"problem_statement": problem_statement}
        )
        
        # Update telemetry
        agent_run.status = AgentRunStatus.COMPLETED
        agent_run.latency_ms = latency_ms
        agent_run.tokens_used = tokens
        db.commit()
        
        # Update Graph state
        state["execution_plan"] = f"Domain: {output.domain} | Complexity: {output.complexity_scale}"
        state["product_data"] = {
            "domain": output.domain,
            "complexity_scale": output.complexity_scale,
            "focus_areas": output.focus_areas,
            "technical_constraints": output.technical_constraints
        }
        
    except Exception as e:
        logger.error(f"Supervisor Node execution failed: {str(e)}")
        if agent_run:
            agent_run.status = AgentRunStatus.FAILED
            agent_run.error = str(e)
            db.commit()
        raise e
    finally:
        db.close()
        
    return state

# Node: Product Agent
def run_product_agent(state: GraphState) -> GraphState:
    logger.info("Executing Product Agent Node...")
    project_id = state["project_id"]
    problem_statement = state["problem_statement"]
    product_meta = state["product_data"]
    
    db = SessionLocal()
    agent_run = None
    try:
        agent_run = AgentRun(
            project_id=project_id,
            agent_type=AgentType.PRODUCT,
            status=AgentRunStatus.STARTED
        )
        db.add(agent_run)
        db.commit()
        db.refresh(agent_run)
        
        # Execute Product Agent
        product_agent = ProductAgent()
        output, latency_ms, tokens = product_agent.execute(
            user_content=problem_statement,
            prompt_vars={
                "problem_statement": problem_statement,
                "domain": product_meta["domain"],
                "complexity_scale": product_meta["complexity_scale"],
                "focus_areas": ", ".join(product_meta["focus_areas"])
            }
        )
        
        # Serialize to Page database model
        page_content = {
            "vision": output.vision,
            "personas": [p.model_dump() for p in output.personas],
            "features": [f.model_dump() for f in output.features],
            "nfrs": [n.model_dump() for n in output.nfrs]
        }
        
        # Check if page already exists, otherwise create
        page = db.query(Page).filter(
            Page.project_id == project_id,
            Page.agent_type == AgentType.PRODUCT
        ).first()
        
        if page:
            page.content_json = page_content
            page.version += 1
        else:
            page = Page(
                project_id=project_id,
                agent_type=AgentType.PRODUCT,
                title="Product Plan & Vision",
                content_json=page_content
            )
            db.add(page)
            
        # Update telemetry
        agent_run.status = AgentRunStatus.COMPLETED
        agent_run.latency_ms = latency_ms
        agent_run.tokens_used = tokens
        db.commit()
        
        # Save payload to state for downstream consumption
        state["product_data"] = page_content
        
    except Exception as e:
        logger.error(f"Product Agent Node execution failed: {str(e)}")
        if agent_run:
            agent_run.status = AgentRunStatus.FAILED
            agent_run.error = str(e)
            db.commit()
        raise e
    finally:
        db.close()
        
    return state

# Node: System Design Agent
def run_system_design_agent(state: GraphState) -> GraphState:
    logger.info("Executing System Design Agent Node...")
    project_id = state["project_id"]
    product_data = state["product_data"]
    
    db = SessionLocal()
    agent_run = None
    try:
        agent_run = AgentRun(
            project_id=project_id,
            agent_type=AgentType.SYSTEM_DESIGN,
            status=AgentRunStatus.STARTED
        )
        db.add(agent_run)
        db.commit()
        db.refresh(agent_run)
        
        # Execute System Design Agent
        sys_agent = SystemDesignAgent()
        output, latency_ms, tokens = sys_agent.execute(
            user_content=product_data.get("vision", ""),
            prompt_vars={"product_data": str(product_data)}
        )
        
        # Save HLD page report
        hld_content = {"markdown": output.hld_markdown}
        page = db.query(Page).filter(
            Page.project_id == project_id,
            Page.agent_type == AgentType.SYSTEM_DESIGN
        ).first()
        
        if page:
            page.content_json = hld_content
            page.version += 1
        else:
            page = Page(
                project_id=project_id,
                agent_type=AgentType.SYSTEM_DESIGN,
                title="Systems Design HLD",
                content_json=hld_content
            )
            db.add(page)
            
        # Save structured React Flow canvas
        canvas_payload = {
            "nodes": [n.model_dump() for n in output.canvas.nodes],
            "edges": [e.model_dump() for e in output.canvas.edges],
            "viewport": {"x": 0, "y": 0, "zoom": 1}
        }
        
        canvas = db.query(CanvasState).filter(CanvasState.project_id == project_id).first()
        if canvas:
            canvas.canvas_json = canvas_payload
        else:
            canvas = CanvasState(
                project_id=project_id,
                canvas_json=canvas_payload
            )
            db.add(canvas)
            
        # Update telemetry
        agent_run.status = AgentRunStatus.COMPLETED
        agent_run.latency_ms = latency_ms
        agent_run.tokens_used = tokens
        
        db.commit()
        
        # Save system design text in state for feasibility consumption
        state["system_design_text"] = output.hld_markdown
        
    except Exception as e:
        logger.error(f"System Design Agent Node execution failed: {str(e)}")
        if agent_run:
            agent_run.status = AgentRunStatus.FAILED
            agent_run.error = str(e)
            
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.status = ProjectStatus.FAILED
        db.commit()
        raise e
    finally:
        db.close()
        
    return state

# Node: Market Agent
def run_market_agent(state: GraphState) -> GraphState:
    logger.info("Executing Market Agent Node...")
    project_id = state["project_id"]
    problem_statement = state["problem_statement"]
    
    db = SessionLocal()
    agent_run = None
    try:
        agent_run = AgentRun(
            project_id=project_id,
            agent_type=AgentType.MARKET,
            status=AgentRunStatus.STARTED
        )
        db.add(agent_run)
        db.commit()
        db.refresh(agent_run)
        
        # Execute Market Agent
        market_agent = MarketAgent()
        output, latency_ms, tokens = market_agent.execute(
            user_content=problem_statement,
            prompt_vars={"problem_statement": problem_statement}
        )
        
        # Serialize to Page database model
        page_content = {
            "competitors": [c.model_dump() for c in output.competitors],
            "gaps": output.gaps,
            "differentiation": output.differentiation
        }
        
        # Check if page already exists, otherwise create
        page = db.query(Page).filter(
            Page.project_id == project_id,
            Page.agent_type == AgentType.MARKET
        ).first()
        
        if page:
            page.content_json = page_content
            page.version += 1
        else:
            page = Page(
                project_id=project_id,
                agent_type=AgentType.MARKET,
                title="Competitive Market Research",
                content_json=page_content
            )
            db.add(page)
            
        # Update telemetry
        agent_run.status = AgentRunStatus.COMPLETED
        agent_run.latency_ms = latency_ms
        agent_run.tokens_used = tokens
        db.commit()
        
        # Save payload to state
        state["market_data"] = page_content
        
    except Exception as e:
        logger.error(f"Market Agent Node execution failed: {str(e)}")
        if agent_run:
            agent_run.status = AgentRunStatus.FAILED
            agent_run.error = str(e)
            
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.status = ProjectStatus.FAILED
        db.commit()
        raise e
    finally:
        db.close()
        
    return state

# Node: Feasibility Agent
def run_feasibility_agent(state: GraphState) -> GraphState:
    logger.info("Executing Feasibility Agent Node...")
    project_id = state["project_id"]
    product_data = state["product_data"]
    market_data = state["market_data"]
    
    db = SessionLocal()
    agent_run = None
    try:
        agent_run = AgentRun(
            project_id=project_id,
            agent_type=AgentType.FEASIBILITY,
            status=AgentRunStatus.STARTED
        )
        db.add(agent_run)
        db.commit()
        db.refresh(agent_run)
        
        # Execute Feasibility Agent
        feasibility_agent = FeasibilityAgent()
        output, latency_ms, tokens = feasibility_agent.execute(
            user_content=str(product_data),
            prompt_vars={
                "product_data": str(product_data),
                "market_data": str(market_data)
            }
        )
        
        # Serialize to Page database model
        page_content = {
            "risks": [r.model_dump() for r in output.risks],
            "resource_requirements": output.resource_requirements,
            "technical_feasibility_summary": output.technical_feasibility_summary
        }
        
        # Check if page already exists, otherwise create
        page = db.query(Page).filter(
            Page.project_id == project_id,
            Page.agent_type == AgentType.FEASIBILITY
        ).first()
        
        if page:
            page.content_json = page_content
            page.version += 1
        else:
            page = Page(
                project_id=project_id,
                agent_type=AgentType.FEASIBILITY,
                title="Technical Feasibility Analysis",
                content_json=page_content
            )
            db.add(page)
            
        # Update telemetry
        agent_run.status = AgentRunStatus.COMPLETED
        agent_run.latency_ms = latency_ms
        agent_run.tokens_used = tokens
        db.commit()
        
        # Save payload to state
        state["feasibility_data"] = page_content
        
    except Exception as e:
        logger.error(f"Feasibility Agent Node execution failed: {str(e)}")
        if agent_run:
            agent_run.status = AgentRunStatus.FAILED
            agent_run.error = str(e)
            
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.status = ProjectStatus.FAILED
        db.commit()
        raise e
    finally:
        db.close()
        
    return state

# Node: Roadmap Agent
def run_roadmap_agent(state: GraphState) -> GraphState:
    logger.info("Executing Roadmap Agent Node...")
    project_id = state["project_id"]
    product_data = state["product_data"]
    feasibility_data = state["feasibility_data"]
    
    db = SessionLocal()
    agent_run = None
    try:
        agent_run = AgentRun(
            project_id=project_id,
            agent_type=AgentType.ROADMAP,
            status=AgentRunStatus.STARTED
        )
        db.add(agent_run)
        db.commit()
        db.refresh(agent_run)
        
        # Execute Roadmap Agent
        roadmap_agent = RoadmapAgent()
        output, latency_ms, tokens = roadmap_agent.execute(
            user_content=str(product_data),
            prompt_vars={
                "product_data": str(product_data),
                "feasibility_data": str(feasibility_data)
            }
        )
        
        # Serialize to Page database model
        page_content = {
            "phases": [p.model_dump() for p in output.phases],
            "mvp_scope": output.mvp_scope,
            "v2_scope": output.v2_scope
        }
        
        # Check if page already exists, otherwise create
        page = db.query(Page).filter(
            Page.project_id == project_id,
            Page.agent_type == AgentType.ROADMAP
        ).first()
        
        if page:
            page.content_json = page_content
            page.version += 1
        else:
            page = Page(
                project_id=project_id,
                agent_type=AgentType.ROADMAP,
                title="Milestone & Execution Roadmap",
                content_json=page_content
            )
            db.add(page)
            
        # Update telemetry
        agent_run.status = AgentRunStatus.COMPLETED
        agent_run.latency_ms = latency_ms
        agent_run.tokens_used = tokens
        
        # Update Project Status to DONE (final node)
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.status = ProjectStatus.DONE
            
        db.commit()
        
    except Exception as e:
        logger.error(f"Roadmap Agent Node execution failed: {str(e)}")
        if agent_run:
            agent_run.status = AgentRunStatus.FAILED
            agent_run.error = str(e)
            
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.status = ProjectStatus.FAILED
        db.commit()
        raise e
    finally:
        db.close()
        
    return state

# Compile state graph pipeline mappings
workflow = StateGraph(GraphState)

# Mount node processing steps
workflow.add_node("supervisor", run_supervisor)
workflow.add_node("product", run_product_agent)
workflow.add_node("market", run_market_agent)
workflow.add_node("system_design", run_system_design_agent)
workflow.add_node("feasibility", run_feasibility_agent)
workflow.add_node("roadmap", run_roadmap_agent)

# Set routing transitions
workflow.set_entry_point("supervisor")

# Parallel branch from supervisor to product and market
workflow.add_conditional_edges(
    "supervisor",
    lambda state: ["product", "market"]
)

# System design depends on product design completion
workflow.add_edge("product", "system_design")

# Feasibility node acts as join node synchronizing both branches
workflow.add_edge("system_design", "feasibility")
workflow.add_edge("market", "feasibility")

# Sequential flow for final timeline roadmap
workflow.add_edge("feasibility", "roadmap")
workflow.add_edge("roadmap", END)

app_graph = workflow.compile()
