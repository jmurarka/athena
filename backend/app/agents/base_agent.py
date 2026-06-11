import time
import json
import logging
from typing import Type, TypeVar, Optional, Dict, Any
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate
from app.core.config import settings

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
        Instantiates the LLM based on available API keys in Settings.
        Prioritizes Gemini, then HuggingFace, and falls back to OpenAI.
        """
        if settings.GEMINI_API_KEY:
            logger.info("Initializing Google Gemini (gemini-1.5-flash) Chat Model...")
            from langchain_google_genai import ChatGoogleGenerativeAI
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=settings.GEMINI_API_KEY,
                temperature=self.temperature
            )
        elif settings.HUGGINGFACE_API_KEY:
            logger.info("Initializing HuggingFace Inference API Model...")
            from langchain_huggingface import HuggingFaceEndpoint
            self.llm = HuggingFaceEndpoint(
                repo_id="meta-llama/Meta-Llama-3-8B-Instruct",
                huggingfacehub_api_token=settings.HUGGINGFACE_API_KEY,
                temperature=self.temperature
            )
        else:
            logger.info("Initializing OpenAI ChatOpenAI Model...")
            from langchain_openai import ChatOpenAI
            api_key = settings.OPENAI_API_KEY or "mock-key"
            self.llm = ChatOpenAI(
                model="gpt-4o",
                openai_api_key=api_key,
                temperature=self.temperature,
                model_kwargs={"response_format": {"type": "json_object"}} if self.response_model else None
            )

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
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", sys_message),
            ("human", user_content)
        ])
        
        chain = prompt | self.llm
        
        start_time = time.time()
        try:
            # Invoke chain
            response = chain.invoke({"input": user_content})
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Extract output structures
            # If with_structured_output worked, response is already the Pydantic model
            if self.response_model and isinstance(response, self.response_model):
                return response, latency_ms, 0
                
            # If response is standard message, parse text content as JSON dict
            content = getattr(response, "content", response)
            if isinstance(content, str):
                if self.response_model:
                    # Strip potential markdown json blocks from raw text (e.g. ```json ... ```)
                    cleaned_content = content.strip()
                    if cleaned_content.startswith("```json"):
                        cleaned_content = cleaned_content[7:]
                    if cleaned_content.endswith("```"):
                        cleaned_content = cleaned_content[:-3]
                    cleaned_content = cleaned_content.strip()
                    
                    parsed_json = json.loads(cleaned_content)
                    return self.response_model.model_validate(parsed_json), latency_ms, 0
                return content, latency_ms, 0
                
            return response, latency_ms, 0
            
        except Exception as e:
            logger.error(f"Agent execution failure: {str(e)}")
            raise e
