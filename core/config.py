"""Configuration loading utilities for the Motstandstrener app."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv


load_dotenv()


@dataclass
class OpenAISettings:
    """Holds configuration for the OpenAI Agent SDK."""

    api_key: str
    scenario_agent_model: str = "gpt-5-nano"
    feedback_agent_model: str = "gpt-5-nano"
    reflection_agent_model: str = "gpt-5-nano"
    referee_agent_model: str = "gpt-5-nano"


@dataclass
class AppSettings:
    """Application-level configuration."""

    openai: OpenAISettings


def load_settings() -> AppSettings:
    """Load settings from environment variables and return an AppSettings instance."""

    api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Please add it to your .env file."
        )

    openai_settings = OpenAISettings(
        api_key=api_key,
        scenario_agent_model=os.getenv("SCENARIO_AGENT_MODEL", "gpt-5-nano"),
        feedback_agent_model=os.getenv("FEEDBACK_AGENT_MODEL", "gpt-5-nano"),
        reflection_agent_model=os.getenv("REFLECTION_AGENT_MODEL", "gpt-5-nano"),
        referee_agent_model=os.getenv("REFEREE_AGENT_MODEL", "gpt-5-nano"),
    )
    return AppSettings(openai=openai_settings)
