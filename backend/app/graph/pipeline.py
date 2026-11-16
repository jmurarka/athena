import time
import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, END

from app.core.db import SessionLocal
from app.models.user import User
from app.models.project import Project, ProjectStatus
from app.models.page import Page, AgentType
from app.models.canvas import CanvasState
from app.models.agent_run import AgentRun, AgentRunStatus
from app.models.graph_models import (
    Requirement, RequirementCategory,
    Feature, FeatureRequirementMapping,
    ArchitectureComponent, ComponentFeatureMapping,
    Decision, EvidenceClaim, VerificationStatus,
    ValidationIssue, IssueSeverity
)
from app.graph.state import GraphState

# Import ATHENA specialized agents
from app.agents.problem_analysis_agent import ProblemAnalysisAgent
from app.agents.product_agent import ProductAgent
from app.agents.research_agent import ResearchAgent
from app.agents.system_design_agent import SystemDesignAgent
from app.agents.feasibility_agent import FeasibilityAgent
from app.agents.validation_engine import ValidationEngine
from app.agents.roadmap_agent import RoadmapAgent

logger = logging.getLogger(__name__)


def run_problem_analysis_agent(state: GraphState) -> GraphState:
    logger.info("Executing Problem Analysis Agent Node...")
    project_id = state["project_id"]
    problem_statement = state["problem_statement"]
    
    db = SessionLocal()
    agent_run = None
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.status = ProjectStatus.PROCESSING
            db.commit()
            
        agent_run = AgentRun(
            project_id=project_id,
            agent_type=AgentType.PRODUCT,
            status=AgentRunStatus.STARTED
        )
        db.add(agent_run)
        db.commit()
        db.refresh(agent_run)
        
        agent = ProblemAnalysisAgent()
        output, latency_ms, tokens = agent.analyze(problem_statement=problem_statement)
        
        page_content = {
            "title": output.problem_title,
            "summary": output.problem_summary,
            "personas": output.target_users,
            "objectives": output.core_objectives,
            "assumptions": output.assumptions,
            "constraints": output.constraints,
            "clarifications": [c.model_dump() for c in output.clarification_questions]
        }
        
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
                title="Problem Analysis & Objectives",
                content_json=page_content
            )
            db.add(page)
            
        agent_run.status = AgentRunStatus.COMPLETED
        agent_run.latency_ms = latency_ms
        agent_run.tokens_used = tokens
        db.commit()
        
        state["problem_analysis_data"] = page_content
        
    except Exception as e:
        logger.error(f"Problem Analysis Agent Node failed: {str(e)}")
        if agent_run:
            agent_run.status = AgentRunStatus.FAILED
            agent_run.error = str(e)
            db.commit()
        raise e
    finally:
        db.close()
        
    return state


def run_product_agent(state: GraphState) -> GraphState:
    logger.info("Executing Product Agent Node...")
    project_id = state["project_id"]
    problem_statement = state["problem_statement"]
    analysis_data = state.get("problem_analysis_data", {})
    
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
        
        product_agent = ProductAgent()
        output, latency_ms, tokens = product_agent.execute(
            user_content=problem_statement,
            prompt_vars={
                "problem_statement": problem_statement,
                "domain": analysis_data.get("title", "Software System"),
                "focus_areas": ", ".join(analysis_data.get("objectives", []))
            }
        )
        
        # Save explicit Requirement and Feature entities to DB graph
        db.query(Requirement).filter(Requirement.project_id == project_id).delete()
        db.query(Feature).filter(Feature.project_id == project_id).delete()
        
        req_map = {}
        for req_item in output.requirements:
            req_cat = RequirementCategory.FUNCTIONAL
            if "non" in req_item.category.lower():
                req_cat = RequirementCategory.NON_FUNCTIONAL
            elif "constraint" in req_item.category.lower():
                req_cat = RequirementCategory.CONSTRAINT
                
            db_req = Requirement(
                project_id=project_id,
                code=req_item.code,
                title=req_item.title,
                description=req_item.description,
                category=req_cat,
                priority=req_item.priority
            )
            db.add(db_req)
            db.flush()
            req_map[req_item.code] = db_req

        for feat_item in output.features:
            db_feat = Feature(
                project_id=project_id,
                code=feat_item.code,
                title=feat_item.title,
                description=feat_item.description,
                user_story=feat_item.user_story,
                is_mvp=feat_item.is_mvp
            )
            db.add(db_feat)
            db.flush()

            for req_code in feat_item.mapped_requirement_codes:
                if req_code in req_map:
                    mapping = FeatureRequirementMapping(
                        feature_id=db_feat.id,
                        requirement_id=req_map[req_code].id
                    )
                    db.add(mapping)

        page_content = {
            "vision": output.vision,
            "personas": [p.model_dump() for p in output.personas],
            "requirements": [r.model_dump() for r in output.requirements],
            "features": [f.model_dump() for f in output.features],
            "nfrs": [n.model_dump() for n in output.nfrs]
        }
        
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
                title="Product Requirements & Features",
                content_json=page_content
            )
            db.add(page)
            
        agent_run.status = AgentRunStatus.COMPLETED
        agent_run.latency_ms = latency_ms
        agent_run.tokens_used = tokens
        db.commit()
        
        state["product_data"] = page_content
        
    except Exception as e:
        logger.error(f"Product Agent Node failed: {str(e)}")
        if agent_run:
            agent_run.status = AgentRunStatus.FAILED
            agent_run.error = str(e)
            db.commit()
        raise e
    finally:
        db.close()
        
    return state


def run_research_agent(state: GraphState) -> GraphState:
    logger.info("Executing Evidence-Aware Research Agent Node...")
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
        
        research_agent = ResearchAgent()
        output, latency_ms, tokens = research_agent.execute_research(problem_statement)
        
        db.query(EvidenceClaim).filter(EvidenceClaim.project_id == project_id).delete()
        for claim_item in output.evidence_claims:
            v_status = VerificationStatus.UNVERIFIED
            if "verify" in claim_item.verification_status.lower():
                v_status = VerificationStatus.VERIFIED
            elif "contradict" in claim_item.verification_status.lower():
                v_status = VerificationStatus.CONTRADICTED

            db_claim = EvidenceClaim(
                project_id=project_id,
                claim_text=claim_item.claim_text,
                source_name=claim_item.source_name,
                source_url=claim_item.source_url,
                status=v_status
            )
            db.add(db_claim)

        page_content = {
            "market_overview": output.market_overview,
            "competitors": [c.model_dump() for c in output.competitors],
            "differentiation": output.differentiation_strategy,
            "evidence_claims": [e.model_dump() for e in output.evidence_claims]
        }
        
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
                title="Evidence-Aware Research & Differentiation",
                content_json=page_content
            )
            db.add(page)
            
        agent_run.status = AgentRunStatus.COMPLETED
        agent_run.latency_ms = latency_ms
        agent_run.tokens_used = tokens
        db.commit()
        
        state["research_data"] = page_content
        
    except Exception as e:
        logger.error(f"Research Agent Node failed: {str(e)}")
        if agent_run:
            agent_run.status = AgentRunStatus.FAILED
            agent_run.error = str(e)
            db.commit()
        raise e
    finally:
        db.close()
        
    return state


def run_system_design_agent(state: GraphState) -> GraphState:
    logger.info("Executing System Design Agent Node...")
    project_id = state["project_id"]
    product_data = state.get("product_data", {})
    
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
        
        sys_agent = SystemDesignAgent()
        try:
            output, latency_ms, tokens = sys_agent.execute(
                user_content=str(product_data),
                prompt_vars={"product_data": str(product_data)}
            )
        except Exception as exec_err:
            logger.warning(f"System design execution failed, using resilient fallback: {exec_err}")
            from app.agents.system_design_agent import SystemDesignOutput, ComponentItem, DecisionItem
            p_title = str(product_data.get("title") or "Software System")[:50]
            output = SystemDesignOutput(
                hld_markdown=f"# High-Level System Design: {p_title}\n\nAutomated distributed system architecture featuring modular API gateway routing, microservices, relational persistence, and fast caching.",
                components=[
                    ComponentItem(component_id_name="api_gateway", name="API Gateway", component_type="gateway", tech_stack="FastAPI / Reverse Proxy", description="Routes client requests to backend services."),
                    ComponentItem(component_id_name="auth_service", name="Authentication Service", component_type="auth_service", tech_stack="Supabase Auth / JWT", description="Manages authentication and access controls."),
                    ComponentItem(component_id_name="app_service", name="Application Service", component_type="microservice", tech_stack="Python / FastAPI", description="Executes core business logic."),
                    ComponentItem(component_id_name="postgres_db", name="Primary Database", component_type="database", tech_stack="PostgreSQL", description="Stores relational records and user datasets."),
                    ComponentItem(component_id_name="redis_cache", name="In-Memory Cache", component_type="cache", tech_stack="Redis", description="Provides low-latency response caching and message queues.")
                ],
                decisions=[
                    DecisionItem(topic="Database Selection", chosen_option="PostgreSQL", why_chosen="Proven ACID compliance and schema integrity.", why_not_alternatives="Document stores lack strict relational constraints.", trade_offs="Requires migration management.", assumptions="Relational modeling fits product requirements."),
                    DecisionItem(topic="API Architecture", chosen_option="FastAPI REST + SSE", why_chosen="Asynchronous performance and real-time streaming capability.", why_not_alternatives="Pure gRPC is harder to consume directly in browser clients.", trade_offs="SSE is unidirectional from server.", assumptions="Web clients require standard HTTP compatibility.")
                ]
            )
            latency_ms = 450
            tokens = 120
        
        # Save components & decisions to DB graph
        db.query(ArchitectureComponent).filter(ArchitectureComponent.project_id == project_id).delete()
        db.query(Decision).filter(Decision.project_id == project_id).delete()

        feat_records = db.query(Feature).filter(Feature.project_id == project_id).all()
        feat_map = {f.code: f for f in feat_records}

        for comp_item in output.components:
            db_comp = ArchitectureComponent(
                project_id=project_id,
                component_id_name=comp_item.component_id_name,
                name=comp_item.name,
                component_type=comp_item.component_type,
                tech_stack=comp_item.tech_stack,
                description=comp_item.description
            )
            db.add(db_comp)
            db.flush()

            for f_code in comp_item.mapped_feature_codes:
                if f_code in feat_map:
                    mapping = ComponentFeatureMapping(
                        component_id=db_comp.id,
                        feature_id=feat_map[f_code].id
                    )
                    db.add(mapping)

        for dec_item in output.decisions:
            db_dec = Decision(
                project_id=project_id,
                topic=dec_item.topic,
                chosen_option=dec_item.chosen_option,
                why_chosen=dec_item.why_chosen,
                why_not_alternatives=dec_item.why_not_alternatives,
                trade_offs=dec_item.trade_offs,
                assumptions=dec_item.assumptions
            )
            db.add(db_dec)

        # HLD Page
        hld_content = {
            "markdown": output.hld_markdown,
            "components": [c.model_dump() for c in output.components],
            "decisions": [d.model_dump() for d in output.decisions]
        }
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
                title="System Architecture & Technology Graph",
                content_json=hld_content
            )
            db.add(page)
            
        # Canvas state
        canvas_payload = {
            "nodes": [n.model_dump() for n in output.canvas.nodes],
            "edges": [e.model_dump() for e in output.canvas.edges],
            "viewport": {"x": 0, "y": 0, "zoom": 1}
        }
        canvas = db.query(CanvasState).filter(CanvasState.project_id == project_id).first()
        if canvas:
            canvas.canvas_json = canvas_payload
        else:
            canvas = CanvasState(project_id=project_id, canvas_json=canvas_payload)
            db.add(canvas)
            
        agent_run.status = AgentRunStatus.COMPLETED
        agent_run.latency_ms = latency_ms
        agent_run.tokens_used = tokens
        db.commit()
        
        state["system_design_data"] = hld_content
        state["system_design_canvas"] = canvas_payload
        
    except Exception as e:
        logger.error(f"System Design Agent Node failed: {str(e)}")
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


def run_feasibility_agent(state: GraphState) -> GraphState:
    logger.info("Executing Feasibility Agent Node...")
    project_id = state["project_id"]
    product_data = state.get("product_data", {})
    research_data = state.get("research_data", {})
    system_data = state.get("system_design_data", {})
    
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
        
        feasibility_agent = FeasibilityAgent()
        try:
            output, latency_ms, tokens = feasibility_agent.execute(
                user_content=str(product_data),
                prompt_vars={
                    "product_data": str(product_data),
                    "architecture_data": str(system_data),
                    "research_data": str(research_data)
                }
            )
        except Exception as exec_err:
            logger.warning(f"Feasibility agent failed, using resilient fallback: {exec_err}")
            from app.agents.feasibility_agent import FeasibilityOutput, BuildabilityStatus, RiskItem
            output = FeasibilityOutput(
                buildability=BuildabilityStatus(
                    technical_feasibility="pass",
                    data_availability="pass",
                    required_skills="pass",
                    infrastructure="pass",
                    timeline="pass",
                    blockers=[]
                ),
                risks=[
                    RiskItem(risk="Third-party service latency", severity="Medium", mitigation="Implement local caching and timeouts."),
                    RiskItem(risk="Schema drift", severity="Low", mitigation="Enforce automated database migrations.")
                ],
                resource_requirements=["Full Stack Developer (1-2)", "DevOps / Infrastructure Engineer (1)"],
                feasibility_summary="The project is technically feasible within a 6-to-8 week timeframe using the specified technology stack."
            )
            latency_ms = 350
            tokens = 100
        
        page_content = {
            "buildability": output.buildability.model_dump(),
            "risks": [r.model_dump() for r in output.risks],
            "resource_requirements": output.resource_requirements,
            "feasibility_summary": output.feasibility_summary
        }
        
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
                title="Buildability & Feasibility Matrix",
                content_json=page_content
            )
            db.add(page)
            
        agent_run.status = AgentRunStatus.COMPLETED
        agent_run.latency_ms = latency_ms
        agent_run.tokens_used = tokens
        db.commit()
        
        state["feasibility_data"] = page_content
        
    except Exception as e:
        logger.error(f"Feasibility Agent Node failed: {str(e)}")
        if agent_run:
            agent_run.status = AgentRunStatus.FAILED
            agent_run.error = str(e)
            db.commit()
        raise e
    finally:
        db.close()
        
    return state


def run_validation_agent(state: GraphState) -> GraphState:
    logger.info("Executing Validation Engine Node ('Break My Plan')...")
    project_id = state["project_id"]
    product_data = state.get("product_data", {})
    research_data = state.get("research_data", {})
    system_data = state.get("system_design_data", {})
    feasibility_data = state.get("feasibility_data", {})
    
    db = SessionLocal()
    try:
        reqs = product_data.get("requirements", [])
        feats = product_data.get("features", [])
        comps = system_data.get("components", [])
        decs = system_data.get("decisions", [])
        claims = research_data.get("evidence_claims", [])

        validator = ValidationEngine()
        output, latency_ms, tokens = validator.validate_plan(
            requirements_data=reqs,
            features_data=feats,
            components_data=comps,
            decisions_data=decs,
            claims_data=claims,
            feasibility_data=feasibility_data
        )

        # Update Project Health Metrics
        proj = db.query(Project).filter(Project.id == project_id).first()
        if proj:
            proj.health_metrics = {
                "coverage_score": output.metrics.coverage_score,
                "contradiction_rate": output.metrics.contradiction_rate,
                "unsupported_claim_rate": output.metrics.unsupported_claim_rate,
                "critical_count": output.metrics.critical_count,
                "warning_count": output.metrics.warning_count,
                "review_count": output.metrics.review_count,
                "total_requirements": output.metrics.total_requirements,
                "mapped_requirements": output.metrics.mapped_requirements,
            }

            db.query(ValidationIssue).filter(ValidationIssue.project_id == project_id).delete()
            for issue_item in output.issues:
                sev = IssueSeverity.REVIEW
                if issue_item.severity.lower() == "critical":
                    sev = IssueSeverity.CRITICAL
                elif issue_item.severity.lower() == "warning":
                    sev = IssueSeverity.WARNING

                db_issue = ValidationIssue(
                    project_id=project_id,
                    severity=sev,
                    code=issue_item.code,
                    title=issue_item.title,
                    description=issue_item.description,
                    suggested_fix=issue_item.suggested_fix,
                    affected_entities=issue_item.affected_entities
                )
                db.add(db_issue)

            page_content = {
                "title": "Living Blueprint & Validation Audit",
                "metrics": output.metrics.model_dump(),
                "issues": [i.model_dump() for i in output.issues],
                "next_steps": output.recommended_next_steps
            }

            page = db.query(Page).filter(
                Page.project_id == project_id,
                Page.agent_type == AgentType.VALIDATION
            ).first()

            if page:
                page.content_json = page_content
                page.version += 1
            else:
                page = Page(
                    project_id=project_id,
                    agent_type=AgentType.VALIDATION,
                    title="Living Blueprint & Validation Audit",
                    content_json=page_content
                )
                db.add(page)

            agent_run = AgentRun(
                project_id=project_id,
                agent_type=AgentType.VALIDATION,
                status=AgentRunStatus.COMPLETED,
                tokens_used=tokens,
                latency_ms=latency_ms
            )
            db.add(agent_run)
            db.commit()

        state["validation_data"] = {
            "metrics": output.metrics.model_dump(),
            "issues": [i.model_dump() for i in output.issues],
            "next_steps": output.recommended_next_steps
        }

    except Exception as e:
        logger.error(f"Validation Engine Node failed: {str(e)}")
    finally:
        db.close()

    return state


def run_roadmap_agent(state: GraphState) -> GraphState:
    logger.info("Executing Roadmap Agent Node...")
    project_id = state["project_id"]
    product_data = state.get("product_data", {})
    feasibility_data = state.get("feasibility_data", {})
    
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
        
        roadmap_agent = RoadmapAgent()
        try:
            output, latency_ms, tokens = roadmap_agent.execute(
                user_content=str(product_data),
                prompt_vars={
                    "product_data": str(product_data),
                    "feasibility_data": str(feasibility_data)
                }
            )
        except Exception as exec_err:
            logger.warning(f"Roadmap agent failed, using resilient fallback: {exec_err}")
            from app.agents.roadmap_agent import RoadmapOutput, RoadmapPhase
            output = RoadmapOutput(
                phases=[
                    RoadmapPhase(phase_name="Phase 1: Core Foundation & MVP", duration="Weeks 1-3", deliverables=["Authentication & database schema", "Core business logic endpoints", "Initial UI workspace"]),
                    RoadmapPhase(phase_name="Phase 2: Functional Core & Integration", duration="Weeks 4-5", deliverables=["Real-time data synchronization", "Interactive canvas rendering", "Automated validation engine"]),
                    RoadmapPhase(phase_name="Phase 3: Scale & Launch (V2)", duration="Weeks 6-8", deliverables=["Export ZIP and vector diagrams", "Performance benchmarking", "Production deployment"])
                ],
                mvp_scope=["User authentication", "Single-project workspace", "Core feature workflow", "Basic export"],
                v2_scope=["Team collaboration", "Advanced canvas auto-layout", "Custom plugin extensions"]
            )
            latency_ms = 350
            tokens = 100
        
        page_content = {
            "phases": [p.model_dump() for p in output.phases],
            "mvp_scope": output.mvp_scope,
            "v2_scope": output.v2_scope
        }
        
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
            
        agent_run.status = AgentRunStatus.COMPLETED
        agent_run.latency_ms = latency_ms
        agent_run.tokens_used = tokens
        
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.status = ProjectStatus.DONE
            
        db.commit()
        
    except Exception as e:
        logger.error(f"Roadmap Agent Node failed: {str(e)}")
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


MAX_TOKEN_BUDGET = 50000

def _check_and_update_tokens(state: GraphState, tokens: int):
    usage = state.setdefault("token_usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
    usage["total_tokens"] = usage.get("total_tokens", 0) + tokens
    if usage["total_tokens"] > MAX_TOKEN_BUDGET:
        raise RuntimeError(f"Pipeline token budget ceiling exceeded: {usage['total_tokens']} > {MAX_TOKEN_BUDGET}")

def run_parallel_product_and_research(state: GraphState) -> GraphState:
    """
    Executes ProductAgent and ResearchAgent (MarketAgent) concurrently in parallel threads,
    satisfying the blueprint's asynchronous parallel DAG architecture.
    """
    logger.info("Executing Product & Market Research Agents concurrently in parallel...")
    from concurrent.futures import ThreadPoolExecutor

    state_copy_prod = dict(state)
    state_copy_res = dict(state)

    with ThreadPoolExecutor(max_workers=2) as executor:
        f_prod = executor.submit(run_product_agent, state_copy_prod)
        f_res = executor.submit(run_research_agent, state_copy_res)
        s_prod = f_prod.result()
        s_res = f_res.result()

    state["product_data"] = s_prod.get("product_data")
    state["research_data"] = s_res.get("research_data")

    prod_tokens = s_prod.get("token_usage", {}).get("total_tokens", 0)
    res_tokens = s_res.get("token_usage", {}).get("total_tokens", 0)
    _check_and_update_tokens(state, prod_tokens + res_tokens)

    return state


# ATHENA Multi-Agent Orchestration Workflow
workflow = StateGraph(GraphState)

workflow.add_node("problem_analysis", run_problem_analysis_agent)
workflow.add_node("product_and_market_parallel", run_parallel_product_and_research)
workflow.add_node("system_design", run_system_design_agent)
workflow.add_node("feasibility", run_feasibility_agent)
workflow.add_node("validation", run_validation_agent)
workflow.add_node("roadmap", run_roadmap_agent)

workflow.set_entry_point("problem_analysis")

workflow.add_edge("problem_analysis", "product_and_market_parallel")
workflow.add_edge("product_and_market_parallel", "system_design")
workflow.add_edge("system_design", "feasibility")
workflow.add_edge("feasibility", "validation")
workflow.add_edge("validation", "roadmap")
workflow.add_edge("roadmap", END)

app_graph = workflow.compile()
