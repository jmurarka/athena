import time
import json
import logging
from typing import Type, TypeVar, Optional, Dict, Any
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate
from app.core.config import settings
from app.core.model_provider import get_llm_instance

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)

class BaseAgent:
    """
    Unified base class for all orchestrator agents.
    Manages LLM instances, executes prompt templates, parses structured JSON,
    and records execution metrics (tokens, latency).
    """
    def __init__(
        self,
        system_prompt: str,
        response_model: Optional[Type[T]] = None,
        temperature: float = 0.2
    ):
        self.system_prompt = system_prompt
        self.response_model = response_model
        self.temperature = temperature
        self._init_llm()

    def _init_llm(self):
        """
        Instantiates LLM using model_provider.py model abstraction layer.
        """
        self.llm = get_llm_instance(temperature=self.temperature)

        # Bind Pydantic schema model if structural parser requested
        if self.response_model:
            try:
                self.llm = self.llm.with_structured_output(self.response_model)
            except Exception as e:
                logger.warning(
                    f"Failed to bind structured output schema: {str(e)}. "
                    "Falling back to manual string parsing."
                )


    def execute(self, user_content: str, prompt_vars: Optional[Dict[str, Any]] = None) -> Any:
        """
        Executes prompt templates, tracking latency and returning structured Pydantic configurations.
        """
        if prompt_vars is None:
            prompt_vars = {}
            
        sys_message = self.system_prompt.format(**prompt_vars)
        if self.response_model and "Example format:" not in sys_message:
            props = list(self.response_model.model_fields.keys())
            sys_message += f"\n\nCRITICAL: Output valid JSON strictly with exact snake_case keys: {json.dumps(props)}"
        
        from langchain_core.messages import SystemMessage, HumanMessage
        messages = [SystemMessage(content=sys_message), HumanMessage(content=user_content)]
        
        start_time = time.time()
        try:
            # Invoke LLM
            response = self.llm.invoke(messages)
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Extract output structures
            # If with_structured_output worked, response is already the Pydantic model
            if self.response_model and isinstance(response, self.response_model):
                return response, latency_ms, 0
                
            # If response is standard message, parse text content as JSON dict
            content = getattr(response, "content", response)
            if isinstance(content, str):
                if self.response_model:
                    import re
                    cleaned_content = content.strip()
                    # Try extracting code fence first
                    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned_content, re.DOTALL)
                    if match:
                        cleaned_content = match.group(1).strip()
                    else:
                        # Find outermost JSON object
                        first_brace = cleaned_content.find("{")
                        last_brace = cleaned_content.rfind("}")
                        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                            cleaned_content = cleaned_content[first_brace:last_brace + 1].strip()
                    
                    parsed_json = json.loads(cleaned_content)
                    
                    def normalize_json_keys(obj):
                        if isinstance(obj, dict):
                            new_obj = {}
                            for k, v in obj.items():
                                snake = re.sub(r'(?<!^)(?=[A-Z])', '_', k).lower()
                                if snake == "project_title":
                                    snake = "problem_title"
                                elif snake == "project_summary":
                                    snake = "problem_summary"
                                new_obj[snake] = normalize_json_keys(v)
                                new_obj[k] = normalize_json_keys(v)
                            return new_obj
                        elif isinstance(obj, list):
                            return [normalize_json_keys(x) for x in obj]
                        return obj

                    parsed_json = normalize_json_keys(parsed_json)
                    return self.response_model.model_validate(parsed_json), latency_ms, 0
                return content, latency_ms, 0
                
            return response, latency_ms, 0
            
        except Exception as e:
            logger.error(f"Agent execution failure: {str(e)}")
            raise e
