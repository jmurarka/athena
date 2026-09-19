import logging
import urllib.request
import json
from typing import Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


def is_ollama_available() -> bool:
    """Check if Ollama server is running locally."""
    for _ in range(2):
        try:
            url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/tags"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=8.0) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
    return False


def get_llm_instance(temperature: float = 0.2) -> Any:
    """
    Instantiates an LLM model object adhering to the specified LLM_MODE.
    Modes:
      - 'local': Exclusively uses local model runtimes (Ollama / llama.cpp).
      - 'cloud': Exclusively uses cloud API providers (Gemini / OpenAI / HuggingFace).
      - 'hybrid': Tries local Ollama first; if offline, falls back to available cloud providers.
    """
    mode = settings.LLM_MODE.lower()

    if mode == "local" or mode == "hybrid":
        try:
            logger.info(f"Initializing Local Ollama model '{settings.OLLAMA_MODEL}' at {settings.OLLAMA_BASE_URL}...")
            from langchain_community.chat_models import ChatOllama
            return ChatOllama(
                base_url=settings.OLLAMA_BASE_URL,
                model=settings.OLLAMA_MODEL,
                temperature=temperature,
                format="json",
            )
        except Exception as e:
            logger.warning(f"Failed to initialize ChatOllama: {str(e)}.")
            if mode == "local":
                raise e
        except Exception as e:
            logger.warning(f"Failed to initialize ChatOllama: {str(e)}.")
            if mode == "local":
                raise e

    # Fallback / Cloud Mode
    if settings.GEMINI_API_KEY:
        logger.info("Initializing Google Gemini (gemini-1.5-flash) Cloud Model...")
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=settings.GEMINI_API_KEY,
            temperature=temperature
        )
    elif settings.HUGGINGFACE_API_KEY:
        logger.info("Initializing HuggingFace Inference API Model...")
        from langchain_huggingface import HuggingFaceEndpoint
        return HuggingFaceEndpoint(
            repo_id="meta-llama/Meta-Llama-3-8B-Instruct",
            huggingfacehub_api_token=settings.HUGGINGFACE_API_KEY,
            temperature=temperature
        )
    else:
        logger.info("Initializing OpenAI ChatOpenAI Model...")
        from langchain_openai import ChatOpenAI
        api_key = settings.OPENAI_API_KEY or "mock-key"
        return ChatOpenAI(
            model="gpt-4o",
            openai_api_key=api_key,
            temperature=temperature
        )
