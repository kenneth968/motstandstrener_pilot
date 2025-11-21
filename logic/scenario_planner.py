"""Generates structured scenario suggestions before the chat begins."""

from __future__ import annotations

import json
from typing import Any, Dict, List

from core.openai_client import AgentRegistry
from core.state import ScenarioContext


class ScenarioPlannerService:
    """Calls a planning agent to produce scenario suggestions."""

    def __init__(self, registry: AgentRegistry, agent_name: str = "scenario_planner") -> None:
        self._registry = registry
        self._agent_name = agent_name

    def generate_options(self, context: ScenarioContext, count: int = 3) -> List[Dict[str, Any]]:
        """Return structured scenario suggestions."""

        prompt = f"""
Du designer scenarioer for en motstandstrener og skal gi JSON.

Rolle: {context.role}
Situasjon: {context.situation}
Treningsmål: {context.goal}

Lag {count} forslag på norsk. Returner JSON som:
{{
  "scenarios": [
    {{
      "id": "kort-id",
      "title": "Kort tittel",
      "summary": "2-3 setninger om situasjonen",
      "focus": "Hva brukeren bør øve på",
      "agent_instructions": "Hvordan motpart-agenten skal opptre (tone, rolle, hva de ønsker å oppnå, hvordan de presser brukeren)",
      "opponent_name": "Et kort norsk navn du vil bruke for motparten (f.eks. Reidar, Ingrid, Amar)"
    }}
  ]
}}
Ingen annen tekst enn JSON.
"""

        raw = self._registry.run(self._agent_name, prompt.strip(), max_turns=6)
        options = self._parse_options(raw)
        if not options:
            options = [
                {
                    "id": "fallback-1",
                    "title": "Samtale med motpart som presser på tid",
                    "summary": "Motparten krever raske beslutninger og stiller spørsmål ved prioriteringene dine.",
                    "focus": "Stå i presset og kommunisere tydelige prioriteringer.",
                    "agent_instructions": "Du er en kollega som presser på for raske svar og setter spørsmålstegn ved planene.",
                    "opponent_name": "Reidar",
                }
            ]
        return options[:count]

    @staticmethod
    def _parse_options(raw: str) -> List[Dict[str, Any]]:
        """Parse JSON from the planner output."""

        text = raw.strip()
        if not text:
            return []

        candidate = text
        if not candidate.startswith("{"):
            start = candidate.find("{")
            end = candidate.rfind("}")
            if start != -1 and end != -1:
                candidate = candidate[start : end + 1]

        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            return []

        scenarios = payload.get("scenarios")
        if not isinstance(scenarios, list):
            return []

        parsed: List[Dict[str, Any]] = []
        for item in scenarios:
            if not isinstance(item, dict):
                continue
            if not {"id", "title", "summary", "agent_instructions"} <= item.keys():
                continue
            parsed.append(
                {
                    "id": item["id"],
                    "title": item["title"],
                    "summary": item["summary"],
                    "focus": item.get("focus", ""),
                    "agent_instructions": item["agent_instructions"],
                    "opponent_name": item.get("opponent_name"),
                }
            )
        return parsed
