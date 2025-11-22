"""Agent helpers that wrap the official openai-agents SDK."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional

from agents import Agent, Runner
from agents.memory import Session


@dataclass
class AgentConfig:
    """Declarative description of an agent."""

    name: str
    model: str
    instructions: str
    handoff_targets: Iterable[str] = field(default_factory=list)


class AgentRegistry:
    """
    Keeps track of configured agents and exposes a synchronous runner.

    The agents SDK automatically reads ``OPENAI_API_KEY`` from the environment.
    """

    def __init__(self) -> None:
        self._agents: Dict[str, Agent] = {}

    def register(self, config: AgentConfig) -> None:
        """Register a new agent config and wire up optional handoffs."""

        handoffs: List[Agent] = []
        for target in config.handoff_targets:
            if target not in self._agents:
                raise KeyError(
                    f"Handoff target '{target}' is not registered. "
                    "Register dependent agents first."
                )
            handoffs.append(self._agents[target])

        self._agents[config.name] = Agent(
            name=config.name,
            model=config.model,
            instructions=config.instructions,
            handoffs=handoffs,
        )

    def get(self, name: str) -> Agent:
        """Return a configured Agent instance."""

        if name not in self._agents:
            raise KeyError(f"No agent registered with name '{name}'.")
        return self._agents[name]

    def run(
        self,
        name: str,
        input_text: str,
        *,
        session: Optional[Session] = None,
        max_turns: int = 6,
        profiler: Optional[object] = None,  # Avoid circular import
    ) -> str:
        """Execute an agent by running the async Runner via asyncio.run."""

        agent = self.get(name)

        async def _run() -> str:
            # If we have a profiler, track the raw agent execution
            if profiler:
                with profiler.profile(f"Agent: {name}"):
                    result = await Runner.run(
                        agent,
                        input=input_text,
                        max_turns=max_turns,
                        session=session,
                    )
            else:
                result = await Runner.run(
                    agent,
                    input=input_text,
                    max_turns=max_turns,
                    session=session,
                )
            return (result.final_output or "").strip()

        return asyncio.run(_run())
