"""Session state helpers to keep Streamlit logic tidy and testable."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, MutableMapping, Optional

from agents import SQLiteSession

from core.learning_params import LearningParams, init_params, update_params
from core.sessions import (
    create_session_store,
    replace_session,
    reset_session_store,
)


@dataclass
class ScenarioContext:
    """Stores the scenario the user wants to rehearse."""

    role: str
    situation: str
    goal: str
    scenario_title: Optional[str] = None
    scenario_summary: Optional[str] = None
    agent_instructions: Optional[str] = None
    opponent_name: Optional[str] = None
    difficulty: str = "Medium"
    avatar_path: Optional[str] = None

@dataclass
class ChatTurn:
    """Single turn in the scenario conversation."""

    user: str
    assistant: str


from core.game_state import GameState

SessionState = MutableMapping[str, Any]


def ensure_session_state(state: SessionState) -> None:
    """Populate the Streamlit session_state with initial values."""

    defaults = {
        "step": 1,
        "mode": "training", # "training" or "sparring"
        "scenario_context": None,
        "chat_history": [],
        "feedback": None,
        "reflection_history": [],
        "learning_params": init_params(),
        "agent_sessions": create_session_store(),
        "scenario_options": [],
        "game_state": None, # For sparring mode
        "sparring_loading": False,
    }

    for key, value in defaults.items():
        if key not in state:
            state[key] = value


def set_context(state: SessionState, context: ScenarioContext) -> None:
    """Persist the active scenario context."""

    state["scenario_context"] = asdict(context)


def get_context(state: SessionState) -> Optional[ScenarioContext]:
    """Return the stored scenario context, if any."""

    data = state.get("scenario_context")
    if not data:
        return None
    return ScenarioContext(**data)


def append_chat_turn(state: SessionState, turn: ChatTurn) -> None:
    """Append a turn to the scenario history and bump learning params."""

    state["chat_history"].append(asdict(turn))
    params: LearningParams = state["learning_params"]
    state["learning_params"] = update_params(params, state["chat_history"])


def reset_for_new_scenario(state: SessionState) -> None:
    """Reset transient data to begin a new training round."""

    state["step"] = 1
    state["scenario_context"] = None
    state["chat_history"] = []
    state["feedback"] = None
    state["reflection_history"] = []
    state["learning_params"] = init_params()
    state["agent_sessions"] = reset_session_store(state.get("agent_sessions"))
    state["scenario_options"] = []
    state["sparring_loading"] = False


def complete_scenario(state: SessionState) -> None:
    """Move from scenario chat to feedback."""

    state["step"] = 4


def move_to_reflection(state: SessionState) -> None:
    """Advance to the reflection step."""

    state["step"] = 5


def add_reflection_turn(state: SessionState, turn: ChatTurn) -> None:
    """Append to the reflection chat log."""

    state["reflection_history"].append(asdict(turn))


def get_chat_history(state: SessionState) -> List[Dict[str, str]]:
    """Return the raw chat history list."""

    return state["chat_history"]


def get_reflection_history(state: SessionState) -> List[Dict[str, str]]:
    """Return the raw reflection history list."""

    return state["reflection_history"]


def get_agent_session(state: SessionState, name: str):
    """Return the SQLiteSession associated with an agent."""

    return state["agent_sessions"][name]


def refresh_agent_session(state: SessionState, name: str) -> None:
    """Clear and recreate a specific agent session."""

    replace_session(state["agent_sessions"], name)

def apply_scenario_details(
    state: SessionState,
    *,
    title: str,
    summary: str,
    agent_instructions: str,
    opponent_name: Optional[str] = None,
    difficulty: str = "Medium",
    avatar_path: Optional[str] = None,
) -> None:
    """Merge generated scenario metadata into the stored context."""

    context = get_context(state)
    if not context:
        raise RuntimeError("Scenario context missing; cannot apply details.")
    data = asdict(context)
    data.update(
        {
            "scenario_title": title,
            "scenario_summary": summary,
            "agent_instructions": agent_instructions,
            "opponent_name": opponent_name,
            "difficulty": difficulty,
            "avatar_path": avatar_path,
        }
    )
    state["scenario_context"] = data
