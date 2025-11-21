"""Scenario agent helpers for the resistance-training phase."""

from __future__ import annotations

from agents import SQLiteSession

from core.learning_params import LearningParams
from core.openai_client import AgentRegistry
from core.state import ScenarioContext


def _format_learning_profile(params: LearningParams) -> str:
    # Format the named parameters for the prompt
    return f"Resilience (Stamina): {params['resilience']:.2f}, Clarity: {params['clarity']:.2f}, Empathy: {params['empathy']:.2f}"


def _build_base_prompt(context: ScenarioContext, learning_params: LearningParams) -> str:
    persona_instructions = (
        context.agent_instructions
        or "Du er motparten i en krevende samtale og trener brukerens motstandsdyktighet."
    )
    learning_profile = _format_learning_profile(learning_params)
    summary = context.scenario_summary or "Ingen ekstra beskrivelse"
    opponent = context.opponent_name or "Motstandstrener"
    
    # Difficulty logic
    difficulty = getattr(context, "difficulty", "Medium")
    difficulty_instruction = ""
    if difficulty == "Easy":
        difficulty_instruction = "MODE: EASY. Be cooperative. Accept reasonable explanations quickly. Do not push back unless the user is rude."
    elif difficulty == "Medium":
        difficulty_instruction = "MODE: MEDIUM. Be skeptical. Require clear arguments. Remain professional but firm."
    elif difficulty == "Hard":
        difficulty_instruction = "MODE: HARD. Be stubborn, emotional, and difficult. Interrupt frequently. Interpret ambiguity negatively. Do not give in easily."

    return f"""
### SYSTEM INSTRUCTION: ROLEPLAY
You are roleplaying as **{opponent}**.
The User is roleplaying as **{context.role}**.

**YOUR GOAL**:
Provide realistic resistance training for the User. You must stay in character as {opponent} at all times.
Do NOT act as a coach or advisor. Act ONLY as the character.

**SCENARIO CONTEXT**:
- **Your Character**: {opponent} ({persona_instructions})
- **Situation**: {context.situation}
- **User's Goal**: {context.goal}
- **Scenario**: {context.scenario_title}
- **Summary**: {summary}
- **Difficulty**: {difficulty}

**ADAPTATION PROFILE (Hidden)**:
{learning_profile}
(Use this to adjust your intensity, but do not mention it).

**DIFFICULTY INSTRUCTIONS**:
{difficulty_instruction}

**RULES**:
1.  **NEVER** break character.
2.  **NEVER** speak for the User.
3.  **NEVER** critique the User during the chat.
4.  Keep responses concise (2-4 sentences).
5.  Be direct and challenging, but realistic.
""".strip()


class ScenarioAgentService:
    """Encapsulates the prompts that drive the scenario chat."""

    def __init__(self, registry: AgentRegistry, agent_name: str = "scenario") -> None:
        self._registry = registry
        self._agent_name = agent_name

    def run_turn(
        self,
        context: ScenarioContext,
        learning_params: LearningParams,
        user_message: str,
        session: SQLiteSession,
    ) -> str:
        """
        Ask the scenario agent to respond to the user's latest message.

        Args:
            context: Scenario metadata supplied in Step 1.
            learning_params: Adaptive profile influencing tone and tempo.
            user_message: The current user input.
            session: SQLiteSession that stores this scenario's memory.
        """

        base_prompt = _build_base_prompt(context, learning_params)
        prompt = f"""
{base_prompt}

Brukerens siste melding:
{user_message}
"""

        return self._registry.run(
            self._agent_name,
            prompt.strip(),
            session=session,
        )

    def start_scenario(
        self,
        context: ScenarioContext,
        learning_params: LearningParams,
        session: SQLiteSession,
    ) -> str:
        """Ask the agent to open the scene with context and the first challenge."""

        base_prompt = _build_base_prompt(context, learning_params)
        prompt = f"""
{base_prompt}

Oppgave: Skriv kun den første replikken fra motparten som setter tydelig motstand.
- Ikke beskriv bakgrunnen på nytt.
- Hopp rett inn i konflikten.
"""
        return self._registry.run(
            self._agent_name,
            prompt.strip(),
            session=session,
        )
