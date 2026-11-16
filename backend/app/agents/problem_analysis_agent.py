import hashlib
import json
import logging
from typing import List, Optional, Union
from pydantic import BaseModel, Field, field_validator
from app.agents.base_agent import BaseAgent
from app.core.config import settings

logger = logging.getLogger(__name__)

# Fallback in-memory cache for local execution
_DECOMPOSITION_MEMORY_CACHE = {}


class ClarificationQuestion(BaseModel):
    question: str = Field(description="Targeted clarification question for missing/ambiguous details.")
    rationale: str = Field(default="Clarification needed for scoping.", description="Why this detail matters for project planning.")


class ProblemAnalysisOutput(BaseModel):
    problem_title: str = Field(default="Athena Project Plan", description="Clean, concise title of the project idea.")
    problem_summary: str = Field(default="", description="Structured breakdown of the problem statement.")
    target_users: List[str] = Field(default_factory=list, description="List of primary and secondary user personas.")
    core_objectives: List[str] = Field(default_factory=list, description="Key measurable objectives of the system.")
    assumptions: List[str] = Field(default_factory=list, description="Implicit or explicit assumptions made.")
    constraints: List[str] = Field(default_factory=list, description="Technical, budget, offline, or regulatory constraints.")
    clarification_questions: List[ClarificationQuestion] = Field(
        default_factory=list,
        description="Targeted questions if the problem input is ambiguous."
    )

    @field_validator("target_users", mode="before")
    @classmethod
    def parse_target_users(cls, v):
        if isinstance(v, list):
            res = []
            for item in v:
                if isinstance(item, dict):
                    name = item.get("name") or item.get("role") or item.get("user") or str(item)
                    desc = item.get("description") or item.get("desc") or ""
                    res.append(f"{name}: {desc}" if desc else name)
                elif isinstance(item, str):
                    res.append(item)
                else:
                    res.append(str(item))
            return res
        return v

    @field_validator("core_objectives", "assumptions", "constraints", mode="before")
    @classmethod
    def parse_string_lists(cls, v):
        if isinstance(v, list):
            res = []
            for item in v:
                if isinstance(item, dict):
                    val = item.get("title") or item.get("description") or item.get("name") or item.get("text") or str(item)
                    res.append(str(val))
                elif isinstance(item, str):
                    res.append(item)
                else:
                    res.append(str(item))
            return res
        return v

    @field_validator("clarification_questions", mode="before")
    @classmethod
    def parse_clarification_questions(cls, v):
        if isinstance(v, list):
            res = []
            for item in v:
                if isinstance(item, str):
                    res.append({"question": item, "rationale": "Clarification needed for project scoping."})
                elif isinstance(item, dict):
                    res.append(item)
            return res
        return v


PROBLEM_ANALYSIS_SYSTEM_PROMPT = """You are ATHENA's Problem Analysis Agent.
Your task is to analyze a raw problem statement or project idea submitted by a user and convert it into a structured problem definition.

Deconstruct the input into:
1. Concise project title
2. Clear problem summary
3. Target user personas (students, developers, enterprises, etc.)
4. Core system objectives
5. Key assumptions
6. Known constraints (e.g. local-first, low budget, offline operation)
7. Clarification questions if the input is vague or missing critical context.

Output strictly in valid JSON matching the requested schema.
"""


class ProblemAnalysisAgent(BaseAgent):
    def __init__(self, temperature: float = 0.2):
        super().__init__(
            system_prompt=PROBLEM_ANALYSIS_SYSTEM_PROMPT,
            response_model=ProblemAnalysisOutput,
            temperature=temperature
        )

    def analyze(self, problem_statement: str):
        # Check SHA-256 cache (Redis with in-memory fallback for 24h TTL)
        sha_hash = hashlib.sha256(problem_statement.strip().encode("utf-8")).hexdigest()
        cache_key = f"athena:decomp:{sha_hash}"

        # 1. Try Redis cache
        if settings.REDIS_URL:
            try:
                import redis
                r = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True, socket_timeout=1.0)
                cached_raw = r.get(cache_key)
                if cached_raw:
                    logger.info(f"Decomposition cache HIT in Redis for SHA {sha_hash[:8]}")
                    cached_data = json.loads(cached_raw)
                    return ProblemAnalysisOutput.model_validate(cached_data), 5, 0
            except Exception:
                pass

        # 2. Try in-memory fallback cache
        if cache_key in _DECOMPOSITION_MEMORY_CACHE:
            logger.info(f"Decomposition cache HIT in memory for SHA {sha_hash[:8]}")
            return ProblemAnalysisOutput.model_validate(_DECOMPOSITION_MEMORY_CACHE[cache_key]), 5, 0

        # Execute LLM reasoning
        output, latency, tokens = self.execute(user_content=problem_statement)

        # Store in cache with 24-hour TTL (86400 seconds)
        try:
            dumped = output.model_dump()
            _DECOMPOSITION_MEMORY_CACHE[cache_key] = dumped
            if settings.REDIS_URL:
                try:
                    import redis
                    r = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True, socket_timeout=1.0)
                    r.setex(cache_key, 86400, json.dumps(dumped))
                except Exception:
                    pass
        except Exception:
            pass

        return output, latency, tokens
