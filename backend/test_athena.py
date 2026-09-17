import sys
import logging
from app.core.config import settings
from app.core.model_provider import get_llm_instance
from app.agents.problem_analysis_agent import ProblemAnalysisAgent
from app.agents.product_agent import ProductAgent
from app.agents.validation_engine import ValidationEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_athena")

def main():
    print("=" * 60)
    print("⚡ ATHENA Platform Agent Pipeline Verification")
    print(f"Current LLM Mode: {settings.LLM_MODE}")
    print(f"Ollama URL: {settings.OLLAMA_BASE_URL} (Model: {settings.OLLAMA_MODEL})")
    print("=" * 60)

    test_input = "I want to build an open-source AI system that detects fake news and analyzes source credibility."

    # 1. Test Problem Analysis Agent
    print("\n[1/3] Testing Problem Analysis Agent...")
    try:
        problem_agent = ProblemAnalysisAgent()
        p_output, p_latency, p_tokens = problem_agent.analyze(test_input)
        print(f"✅ Success! Title: {p_output.problem_title} (Latency: {p_latency}ms)")
        print(f"Summary: {p_output.problem_summary}")
        print(f"Constraints: {p_output.constraints}")
    except Exception as e:
        print(f"❌ Problem Analysis Agent failed: {e}")
        return

    # 2. Test Product Agent
    print("\n[2/3] Testing Product Agent (Requirement Graph Generation)...")
    try:
        product_agent = ProductAgent()
        prod_output, prod_latency, prod_tokens = product_agent.execute(
            user_content=test_input,
            prompt_vars={
                "problem_statement": test_input,
                "domain": p_output.problem_title,
                "focus_areas": ", ".join(p_output.core_objectives)
            }
        )
        print(f"✅ Success! Generated {len(prod_output.requirements)} Requirements & {len(prod_output.features)} Features (Latency: {prod_latency}ms)")
        for r in prod_output.requirements[:3]:
            print(f"   • {r.code}: {r.title} ({r.category})")
    except Exception as e:
        print(f"❌ Product Agent failed: {e}")
        return

    # 3. Test Validation Engine ("Break My Plan")
    print("\n[3/3] Testing Validation Engine ('Break My Plan')...")
    try:
        validator = ValidationEngine()
        val_output, val_latency, val_tokens = validator.validate_plan(
            requirements_data=[r.model_dump() for r in prod_output.requirements],
            features_data=[f.model_dump() for f in prod_output.features],
            components_data=[{"name": "News Classifier Service", "type": "microservice", "tech": "Python / FastAPI"}],
            decisions_data=[{"topic": "Model Hosting", "chosen_option": "Local Ollama"}],
            claims_data=[],
            feasibility_data={}
        )
        print(f"✅ Success! Requirement Coverage: {val_output.metrics.coverage_score * 100:.1f}% (Latency: {val_latency}ms)")
        print(f"   • Critical Alerts: {val_output.metrics.critical_count}, Warnings: {val_output.metrics.warning_count}")
        for issue in val_output.issues[:2]:
            print(f"   [{issue.severity.upper()}] {issue.title}: {issue.description}")
    except Exception as e:
        print(f"❌ Validation Engine failed: {e}")
        return

    print("\n" + "=" * 60)
    print("🎉 All ATHENA Agents Verified Successfully!")
    print("=" * 60)

if __name__ == "__main__":
    main()
