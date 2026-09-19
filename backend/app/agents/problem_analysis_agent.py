from typing import List, Optional, Union
from pydantic import BaseModel, Field, field_validator
from app.agents.base_agent import BaseAgent


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
        return self.execute(user_content=problem_statement)
