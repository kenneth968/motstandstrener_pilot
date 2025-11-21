"""Reflection agent that guides the optional debrief chat."""

from __future__ import annotations

from agents import SQLiteSession

from core.openai_client import AgentRegistry
from core.state import ScenarioContext


class ReflectionAgentService:
    """Guides the reflection phase with one question at a time."""

    def __init__(self, registry: AgentRegistry, agent_name: str = "reflection") -> None:
        self._registry = registry
        self._agent_name = agent_name

    def run_turn(
        self,
        context: ScenarioContext,
        user_message: str,
        session: SQLiteSession,
    ) -> str:
        """Return the next reflection prompt or acknowledgement."""

        prompt = f"""
Du er en rolig refleksjonsveileder.
Brukerens rolle: {context.role}
Situasjon: {context.situation}
Treningsmål: {context.goal}

Still ett spørsmål av gangen, lytt og hjelp brukeren å hente ut læring uten å dømme.
Brukerens siste refleksjon:
{user_message}
"""
        return self._registry.run(
            self._agent_name,
            prompt.strip(),
            session=session,
        )

    def start_reflection(
        self,
        context: ScenarioContext,
        session: SQLiteSession,
        scenario_was_skipped: bool = False,
    ) -> str:
        """Generate an opening reflection question."""
        
        if scenario_was_skipped:
            prompt = f"""
Du er en rolig refleksjonsveileder.
Brukeren valgte å avslutte scenarioet før det kom ordentlig i gang.

Oppgave: Spør vennlig og nysgjerrig om hva som gjorde at de valgte å stoppe.
Eksempel: "Jeg ser at du avsluttet tidlig. Var det noe spesielt som gjorde at du valgte å stoppe, eller ville du bare teste funksjonen?"
"""
        else:
            prompt = f"""
Du er en rolig refleksjonsveileder.
Brukerens rolle: {context.role}
Situasjon: {context.situation}
Treningsmål: {context.goal}

Oppgave: Still et åpent, inviterende spørsmål for å starte refleksjonen.
Spørsmålet bør handle om hvordan brukeren opplevde situasjonen.
Eksempel: "Hvordan føltes det å møte denne motstanden?" eller "Hva sitter du igjen med etter denne samtalen?"
"""
        return self._registry.run(
            self._agent_name,
            prompt.strip(),
            session=session,
        )
