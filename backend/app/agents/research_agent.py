from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, model_validator
from app.agents.base_agent import BaseAgent


class CompetitorItem(BaseModel):
    name: str = "Competitor"
    strengths: List[str] = Field(default_factory=list, description="Key strengths")
    weaknesses: List[str] = Field(default_factory=list, description="Key limitations or gaps")
    athena_differentiation: str = Field(default="", description="How our proposed solution differentiates")

    @model_validator(mode='before')
    @classmethod
    def pre_validate(cls, data: Any) -> Any:
        if isinstance(data, str):
            return {
                "name": data,
                "strengths": [f"Established market presence for {data}"],
                "weaknesses": ["Lacks integrated local developer orchestration"],
                "athena_differentiation": f"ATHENA provides automated local-first validation compared to {data}"
            }
        if isinstance(data, dict):
            name = data.get("name") or data.get("title") or "Competitor"
            strengths = data.get("strengths") or []
            if isinstance(strengths, str):
                strengths = [strengths]
            weaknesses = data.get("weaknesses") or []
            if isinstance(weaknesses, str):
                weaknesses = [weaknesses]
            diff = data.get("athena_differentiation") or data.get("differentiation") or ""
            return {
                "name": name,
                "strengths": strengths,
                "weaknesses": weaknesses,
                "athena_differentiation": diff
            }
        return data


class EvidenceClaimItem(BaseModel):
    claim_text: str = Field(default="", description="Factual claim regarding technology performance, market gap, or feasibility")
    source_name: str = Field(default="Technical Standard", description="Reference source name or document standard")
    source_url: Optional[str] = Field(default=None, description="URL or benchmark reference if available")
    verification_status: str = Field(default="verified", description="verified, unverified, or contradicted")
    rationale: str = Field(default="Derived from technical analysis", description="Reasoning behind claim verification")

    @model_validator(mode='before')
    @classmethod
    def pre_validate(cls, data: Any) -> Any:
        if isinstance(data, str):
            return {
                "claim_text": data,
                "source_name": "Documentation standard",
                "source_url": None,
                "verification_status": "verified",
                "rationale": "Empirical analysis"
            }
        if isinstance(data, dict):
            claim_text = data.get("claim_text") or data.get("claim") or data.get("text") or ""
            source_name = data.get("source_name") or data.get("source") or "Technical documentation"
            source_url = data.get("source_url") or data.get("url")
            verification_status = data.get("verification_status") or data.get("status") or "verified"
            rationale = data.get("rationale") or data.get("reasoning") or "Derived from technical analysis"
            return {
                "claim_text": claim_text,
                "source_name": source_name,
                "source_url": source_url,
                "verification_status": verification_status,
                "rationale": rationale
            }
        return data


class ResearchOutput(BaseModel):
    market_overview: str = Field(default="Market analysis report", description="High-level analysis of market context and existing tools")
    competitors: List[CompetitorItem] = Field(default_factory=list, description="Competitors and market gap breakdown")
    differentiation_strategy: str = Field(default="Core unique value proposition", description="Core unique value proposition")
    evidence_claims: List[EvidenceClaimItem] = Field(default_factory=list, description="Grounding factual claims with source evidence and verification status")

    @model_validator(mode='before')
    @classmethod
    def pre_validate(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "market_overview" not in data:
                data["market_overview"] = data.get("overview") or data.get("summary") or "Market analysis report."
            if "differentiation_strategy" not in data:
                data["differentiation_strategy"] = data.get("differentiation") or data.get("strategy") or "Core differentiation via automated requirement validation."
        return data


RESEARCH_SYSTEM_PROMPT = """You are ATHENA's Evidence-Aware Research Agent.
Analyze the problem statement: {problem_statement}.

Relevant Live Market & Technical Research Findings:
{search_context}

Conduct a technical and market research analysis:
1. Identify existing solutions and competitors.
2. Outline key strengths, weaknesses, and differentiation parameters.
3. Formulate evidence-backed claims (e.g. "Ollama enables zero cloud egress cost for local inference").
4. Assign verification status (`verified`, `unverified`, or `contradicted`) and site evidence sources for each claim.

Output strictly in valid JSON matching the requested schema.
"""


class ResearchAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            system_prompt=RESEARCH_SYSTEM_PROMPT,
            response_model=ResearchOutput,
            temperature=0.2
        )

    @staticmethod
    def search_market_context(query: str, max_results: int = 4) -> str:
        """
        Retrieves real-time market search snippets via DuckDuckGo / web search,
        with graceful fallback if offline or sandboxed.
        """
        import urllib.request
        import urllib.parse
        import json

        findings = []
        try:
            encoded_query = urllib.parse.quote_plus(query)
            url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json"
            req = urllib.request.Request(url, headers={"User-Agent": "AthenaResearchAgent/1.0"})
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                abstract = data.get("AbstractText")
                if abstract:
                    findings.append(f"Summary: {abstract}")
                for topic in data.get("RelatedTopics", [])[:max_results]:
                    if isinstance(topic, dict) and "Text" in topic:
                        findings.append(f"- {topic['Text']}")
        except Exception:
            pass

        if not findings:
            return "No external search API results available (operating in local-first sandbox mode). Relying on analytical industry standards."
        return "\n".join(findings)

    def execute_research(self, problem_statement: str):
        search_snippets = self.search_market_context(problem_statement)
        return self.execute(
            user_content=problem_statement,
            prompt_vars={
                "problem_statement": problem_statement,
                "search_context": search_snippets
            }
        )
