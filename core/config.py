"""Configuration loading utilities for the Motstandstrener app."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

import streamlit as st
from dotenv import load_dotenv


load_dotenv()


@dataclass
class OpenAISettings:
    """Holds configuration for the OpenAI Agent SDK."""

    api_key: str
    scenario_agent_model: str = "gpt-4o-mini"
    feedback_agent_model: str = "gpt-4o-mini"
    reflection_agent_model: str = "gpt-4o-mini"
    referee_agent_model: str = "gpt-4o-mini"

@dataclass
class AppSettings:
    """Application-level configuration."""

    openai: OpenAISettings


def load_settings() -> AppSettings:
    """Load settings from environment variables or Streamlit secrets."""

    api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    # Fallback to Streamlit secrets if not in env (for Cloud deployment)
    if not api_key and hasattr(st, "secrets") and "OPENAI_API_KEY" in st.secrets:
        api_key = st.secrets["OPENAI_API_KEY"]

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Please add it to your .env file or Streamlit secrets."
        )

    openai_settings = OpenAISettings(
        api_key=api_key,
        scenario_agent_model=os.getenv("SCENARIO_AGENT_MODEL", "gpt-4o-mini"),
        feedback_agent_model=os.getenv("FEEDBACK_AGENT_MODEL", "gpt-4o-mini"),
        reflection_agent_model=os.getenv("REFLECTION_AGENT_MODEL", "gpt-4o-mini"),
        referee_agent_model=os.getenv("REFEREE_AGENT_MODEL", "gpt-4o-mini"),
    )
    return AppSettings(openai=openai_settings)
