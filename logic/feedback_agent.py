"""Agent responsible for concise scenario feedback."""

from __future__ import annotations

from typing import Dict, Iterable, List

from agents import SQLiteSession

from core.openai_client import AgentRegistry
from core.state import ScenarioContext


def _history_markdown(history: Iterable[Dict[str, str]]) -> str:
    lines: List[str] = []
    for turn in history:
        lines.append(f"Bruker: {turn['user']}")
        lines.append(f"Trener: {turn['assistant']}")
    return "\n".join(lines)


class FeedbackAgentService:
    """Produces bullet-style feedback once the scenario ends."""

    def __init__(self, registry: AgentRegistry, agent_name: str = "feedback") -> None:
        self._registry = registry
        self._agent_name = agent_name

    def generate(
        self,
        context: ScenarioContext,
        history: Iterable[Dict[str, str]],
        session: SQLiteSession,
        profiler: object = None,
    ) -> str:
        """Ask the feedback agent for 3–5 short observations."""

        # Check if there is enough history to generate feedback
        history_list = list(history)
        if len(history_list) < 2:
            return "Du avsluttet scenarioet før vi kom ordentlig i gang. Start gjerne et nytt scenario for å få tilbakemelding."

        chat_summary = _history_markdown(history_list)
        prompt = f"""
Du er en varm, klok og støttende veileder i motstandstrening.
Din oppgave er å gi brukeren en følelse av mestring, samtidig som du peker på muligheter for vekst.

Rolle: {context.role}
Situasjon: {context.situation}
Treningsmål: {context.goal}

Dialog:
{chat_summary}

Instruksjoner for tilbakemelding:
1.  **Anerkjennelse**: Start med å nevne noe brukeren gjorde bra (f.eks. "Jeg likte hvordan du...").
2.  **Forslag**: Gi 2-3 konkrete, vennlige forslag til neste gang. Bruk formuleringer som "Du kan prøve å..." eller "Det kan være spennende å utforske...".
3.  **Tone**: Vær ydmyk. Du sitter ikke med fasiten. Unngå ord som "feil", "dårlig", "burde".
4.  **Format**: Skriv på norsk, bruk punktliste.
"""
        return self._registry.run(
            self._agent_name,
            prompt.strip(),
            session=session,
            max_turns=4,
            profiler=profiler,
        )
