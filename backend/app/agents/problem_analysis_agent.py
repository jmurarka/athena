from typing import List, Optional
from pydantic import BaseModel, Field
from app.agents.base_agent import BaseAgent


class ClarificationQuestion(BaseModel):
    question: str = Field(description="Targeted clarification question for missing/ambiguous details.")
    rationale: str = Field(description="Why this detail matters for project planning.")


class ProblemAnalysisOutput(BaseModel):
    problem_title: str = Field(description="Clean, concise title of the project idea.")
    problem_summary: str = Field(description="Structured breakdown of the problem statement.")
    target_users: List[str] = Field(description="List of primary and secondary user personas.")
    core_objectives: List[str] = Field(description="Key measurable objectives of the system.")
    assumptions: List[str] = Field(description="Implicit or explicit assumptions made.")
    constraints: List[str] = Field(description="Technical, budget, offline, or regulatory constraints.")
    clarification_questions: List[ClarificationQuestion] = Field(
        default_factory=list,
        description="Targeted questions if the problem input is ambiguous."
    )


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
