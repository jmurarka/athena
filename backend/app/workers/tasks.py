import logging
from app.workers.celery_app import celery

from app.graph.pipeline import app_graph

logger = logging.getLogger(__name__)

@celery.task(name="app.workers.tasks.run_agentic_pipeline")
def run_agentic_pipeline(project_id: str, problem_statement: str):
    """
    Background worker task to run the LangGraph orchestration flow.
    Runs the pipeline using the compiled graph.
    """
    logger.info(f"Triggering pipeline execution for project {project_id}")
    try:
        initial_state = {
            "project_id": project_id,
            "problem_statement": problem_statement,
            "execution_plan": None,
            "product_data": None,
            "market_data": None,
            "system_design_text": None,
            "system_design_canvas": None,
            "feasibility_data": None,
            "roadmap_data": None,
            "token_usage": {},
            "latency_ms": {}
        }
        
        # Invoke the compiled LangGraph pipeline graph
        result = app_graph.invoke(initial_state)
        
        logger.info(f"Pipeline execution completed successfully for project {project_id}")
        return {
            "project_id": project_id,
            "status": "completed",
            "message": "Orchestrator pipeline executed successfully",
            "result_summary": {
                "execution_plan": result.get("execution_plan"),
                "product_data_keys": list(result.get("product_data", {}).keys()) if result.get("product_data") else [],
                "market_data_keys": list(result.get("market_data", {}).keys()) if result.get("market_data") else [],
                "feasibility_data_keys": list(result.get("feasibility_data", {}).keys()) if result.get("feasibility_data") else [],
                "roadmap_data_keys": list(result.get("roadmap_data", {}).keys()) if result.get("roadmap_data") else []
            }
        }
    except Exception as e:
        logger.error(f"Failed pipeline run: {str(e)}", exc_info=True)
        raise e
