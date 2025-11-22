"""Streamlit entrypoint for the AI-drevet motstandstrener pilot."""

from __future__ import annotations

import random
import os
import time
from typing import Dict, List

import streamlit as st

from core.config import AppSettings, load_settings
from core.openai_client import AgentConfig, AgentRegistry
from core import state as session_state
from core.state import ChatTurn, ScenarioContext, apply_scenario_details
from core.scenarios import PREBUILT_SCENARIOS
from core.game_state import GameState
from core.profiler import Profiler
from logic.feedback_agent import FeedbackAgentService
from logic.reflection_agent import ReflectionAgentService
from logic.scenario_agent import ScenarioAgentService
from logic.scenario_planner import ScenarioPlannerService
from logic.referee_agent import RefereeAgentService
from ui.components import (
    render_header, 
    render_chat_message, 
    render_scenario_card, 
    render_context_sidebar,
    render_scenario_briefing,
    render_scenario_selection_card,
    render_custom_scenario_card,
    render_difficulty_selector
)
from ui.game_components import render_health_bar, render_fight_header, render_round_options, render_round_result


st.set_page_config(page_title="Motstandstrener", layout="wide")


@st.cache_resource
def bootstrap_services(version: str = "2024-11-22-profiling-v1") -> Dict[str, object]:
    """Initialize configuration, agent registry, and service layer instances."""

    settings: AppSettings = load_settings()
    registry = AgentRegistry()
    registry.register(
        AgentConfig(
            name="scenario",
            model=settings.openai.scenario_agent_model,
            instructions="Du er en direkte, men respektfull motpart i en krevende samtale.",
        )
    )
    registry.register(
        AgentConfig(
            name="feedback",
            model=settings.openai.feedback_agent_model,
            instructions="Du skriver korte, støttende observasjoner i punktform.",
        )
    )
    registry.register(
        AgentConfig(
            name="reflection",
            model=settings.openai.reflection_agent_model,
            instructions="Du leder en rolig refleksjonssamtale og stiller ett spørsmål av gangen.",
        )
    )
    registry.register(
        AgentConfig(
            name="scenario_planner",
            model=settings.openai.scenario_agent_model,
            instructions="Du designer korte scenarioforslag i JSON for motstandstrening.",
        )
    )
    registry.register(
        AgentConfig(
            name="referee",
            model=settings.openai.referee_agent_model,
            instructions=(
                "Du er en streng men rettferdig dommer i en verbal boksekamp. "
                "Du svarer ALLTID med gyldig JSON."
            ),
        )
    )

    services = {
        "scenario": ScenarioAgentService(registry, "scenario"),
        "feedback": FeedbackAgentService(registry, "feedback"),
        "reflection": ReflectionAgentService(registry, "reflection"),
        "scenario_planner": ScenarioPlannerService(registry, "scenario_planner"),
        "referee": RefereeAgentService(registry, "referee"),
    }
    return services


services = bootstrap_services()
OPPONENT_NAMES = [
    "Reidar",
    "Ingrid",
    "Marte",
    "Amar",
    "Siv",
    "Leif",
    "Aisha",
    "Håkon",
    "Nora",
    "Jonas",
]
DEFAULT_FORM_VALUES = {
    "role": "Prosjektleder i NAV som håndterer en krevende kollegasamtale",
    "situation": "Jeg skal følge opp en kollega som stadig utfordrer prioriteringene i prosjektet, og vi står foran en viktig frist.",
    "goal": "Jeg vil trene på å sette tydelige grenser og samtidig bevare samarbeidsklimaet.",
}


def _ensure_form_defaults() -> None:
    for key, value in DEFAULT_FORM_VALUES.items():
        state_key = f"form_{key}"
        if state_key not in st.session_state:
            st.session_state[state_key] = value


def _pick_opponent_name(preferred: str | None = None) -> str:
    if preferred:
        return preferred
    return random.choice(OPPONENT_NAMES)


def _render_chat(history: List[Dict[str, str]], assistant_label: str, assistant_avatar: str | None = None) -> None:
    """Render chat history using reusable components."""
    for turn in history:
        user_message = turn.get("user") or ""
        if user_message.strip():
            render_chat_message("user", user_message)
        
        # Use the specific avatar if provided, otherwise default to robot
        avatar = assistant_avatar or "🤖"
        render_chat_message("assistant", turn['assistant'], avatar=avatar)


def render_scenario_selection_step() -> None:
    """Step 1 – Choose from library or create custom."""
    st.subheader("1. Velg treningsscenario")
    st.caption("Velg et ferdig scenario eller lag ditt eget.")
    
    # Grid layout for scenarios
    cols = st.columns(2)
    
    # Render pre-built scenarios
    for i, scenario in enumerate(PREBUILT_SCENARIOS):
        with cols[i % 2]:
            def on_select(s=scenario):
                # Initialize context from the pre-built scenario
                context = ScenarioContext(
                    role=s.role,
                    situation=s.situation,
                    goal=s.goal,
                    scenario_title=s.title,
                    scenario_summary=s.summary,
                    agent_instructions=s.difficulty_modifier, # Base modifier, will be augmented by difficulty logic
                    opponent_name=s.opponent_name, # Use fixed opponent name
                    avatar_path=s.avatar_path # Use specific avatar
                )
                session_state.set_context(st.session_state, context)
                st.session_state.step = 2 # Go to configuration
                st.rerun()
                
            render_scenario_selection_card(scenario, on_select, key=f"scenario_{scenario.id}")

    # Render "Custom" option
    with cols[len(PREBUILT_SCENARIOS) % 2]:
        def on_custom():
            st.session_state.step = 10 # Go to custom setup
            st.rerun()
        render_custom_scenario_card(on_custom, key="scenario_custom")


def render_custom_setup_step() -> None:
    """Step 10 – Custom: capture role, situation, and goal."""
    
    st.subheader("Skreddersy scenario")
    if st.button("⬅ Tilbake til oversikt", type="primary"):
        st.session_state.step = 1
        st.rerun()
        
    st.caption("Beskriv situasjonen du vil øve på. Ingen sensitive personopplysninger.")
    _ensure_form_defaults()

    with st.form("prep_form"):
        role = st.text_input("Hvilken rolle er du i?", key="form_role")
        situation = st.text_area("Beskriv situasjonen kort", key="form_situation")
        goal = st.text_area("Hva vil du trene på?", key="form_goal")
        
        submitted = st.form_submit_button("Hent forslag", type="primary", use_container_width=True)

    if submitted:
        if not (role and situation and goal):
            st.error("Du må fylle ut alle feltene.")
            return

        context = ScenarioContext(role=role, situation=situation, goal=goal)
        session_state.set_context(st.session_state, context)
        with st.spinner("Analyserer situasjonen og lager scenarier..."):
            options = services["scenario_planner"].generate_options(context)
        st.session_state.scenario_options = options
        st.session_state.step = 11 # Go to custom picker
        st.rerun()


def render_custom_picker_step() -> None:
    """Step 11 – Custom: review generated scenario suggestions."""
    
    st.subheader("Velg variant")
    context = session_state.get_context(st.session_state)
    options = st.session_state.get("scenario_options", [])

    if not context or not options:
        st.warning("Noe gikk galt. Prøv igjen.")
        st.session_state.step = 10
        st.rerun()
        return

    # Render sidebar context
    render_context_sidebar(context)

    st.write("Her er tre forslag basert på din situasjon:")

    for option in options:
        def on_choose(opt=option):
            opponent_name = _pick_opponent_name(opt.get("opponent_name"))
            apply_scenario_details(
                st.session_state,
                title=opt["title"],
                summary=opt["summary"],
                agent_instructions=opt["agent_instructions"],
                opponent_name=opponent_name,
            )
            # Instead of going straight to chat, go to configuration
            st.session_state.step = 2 
            st.rerun()

        render_scenario_card(option, on_choose, key=f"card_{option['id']}")

    st.divider()
    if st.button("⬅ Tilbake", use_container_width=True, type="primary"):
        st.session_state.step = 10
        st.rerun()


def render_configuration_step() -> None:
    """Step 2 – Configure difficulty and start."""
    st.subheader("2. Konfigurasjon")
    
    context = session_state.get_context(st.session_state)
    if not context:
        st.session_state.step = 1
        st.rerun()
        return

    render_context_sidebar(context)
    
    st.info(f"Du har valgt: **{context.scenario_title}**")
    
    # Difficulty Selector
    difficulty = render_difficulty_selector(context.difficulty)
    
    # Update context with selected difficulty
    if difficulty != context.difficulty:
        # We need to update the context in session state
        # This is a bit hacky, ideally we'd have a setter
        context.difficulty = difficulty
        session_state.set_context(st.session_state, context)

    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅ Velg et annet scenario", use_container_width=True, type="primary"):
            st.session_state.step = 1
            st.rerun()
            
    with col2:
        if st.button("🚀 Start Trening", type="primary", use_container_width=True):
            # Initialize the session
            session_state.refresh_agent_session(st.session_state, "scenario")
            st.session_state.chat_history = []
            st.session_state.feedback = None
            st.session_state.reflection_history = []
            st.session_state.scenario_options = []
            
            st.session_state.step = 3
            st.rerun()


def render_scenario_step() -> None:
    """Step 3 – interactive scenario chat."""
    
    context = session_state.get_context(st.session_state)
    if not context:
        st.session_state.step = 1
        st.rerun()
        return

    # Layout: Left column for info/controls, Right column for chat
    col_info, col_chat = st.columns([1, 2], gap="large")

    with col_info:
        render_scenario_briefing(context)
        
        st.divider()
        
        # "End Scenario" button in the left column
        if st.button("🏁 Avslutt og få tilbakemelding", type="primary", use_container_width=True):
            session_state.complete_scenario(st.session_state)
            st.rerun()

    with col_chat:
        st.subheader(f"Chat med {context.opponent_name}")
        
        history = session_state.get_chat_history(st.session_state)
        if not history:
            # Start the conversation
            intro = services["scenario"].start_scenario(
                context=context,
                learning_params=st.session_state.learning_params,
                session=session_state.get_agent_session(st.session_state, "scenario"),
                profiler=st.session_state.profiler,
            )
            session_state.append_chat_turn(
                st.session_state, ChatTurn(user="", assistant=intro)
            )
            st.rerun()
            return

        opponent_label = context.opponent_name or "Motstandstrener"
        # Pass the avatar path to the chat renderer
        _render_chat(history, opponent_label, assistant_avatar=context.avatar_path)

        # Input area (always at bottom)
        user_msg = st.chat_input("Skriv ditt svar...")
        
        if user_msg:
            reply = services["scenario"].run_turn(
                context=context,
                learning_params=st.session_state.learning_params,
                user_message=user_msg,
                session=session_state.get_agent_session(st.session_state, "scenario"),
                profiler=st.session_state.profiler,
            )
            session_state.append_chat_turn(
                st.session_state, ChatTurn(user=user_msg, assistant=reply)
            )
            st.rerun()


def render_feedback_step() -> None:
    """Step 4 – generate short-form feedback."""
    
    st.subheader("4. Tilbakemelding")
    context = session_state.get_context(st.session_state)
    if not context:
        st.session_state.step = 1
        st.rerun()
        return

    render_context_sidebar(context)

    if st.session_state.feedback is None:
        with st.spinner("Analyserer samtalen..."):
            session_state.refresh_agent_session(st.session_state, "feedback")
            st.session_state.feedback = services["feedback"].generate(
                context=context,
                history=session_state.get_chat_history(st.session_state),
                session=session_state.get_agent_session(st.session_state, "feedback"),
                profiler=st.session_state.profiler,
            )

    st.success("Her er noen tanker om gjennomføringen:")
    st.markdown(st.session_state.feedback)

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Reflekter over økten", use_container_width=True, type="primary"):
            session_state.refresh_agent_session(st.session_state, "reflection")
            session_state.move_to_reflection(st.session_state)
            st.rerun()
    with col2:
        if st.button("Start nytt scenario", use_container_width=True, type="primary"):
            session_state.reset_for_new_scenario(st.session_state)
            st.rerun()


def render_reflection_step() -> None:
    """Step 5 – optional reflection chat."""
    
    st.subheader("5. Refleksjon")
    context = session_state.get_context(st.session_state)
    if not context:
        st.session_state.step = 1
        st.rerun()
        return

    render_context_sidebar(context)

    history = session_state.get_reflection_history(st.session_state)
    if not history:
        # Check if the previous scenario was actually played
        scenario_history = session_state.get_chat_history(st.session_state)
        scenario_was_skipped = len(scenario_history) < 2

        # Start the reflection conversation
        intro = services["reflection"].start_reflection(
            context=context,
            session=session_state.get_agent_session(st.session_state, "reflection"),
            scenario_was_skipped=scenario_was_skipped,
        )
        session_state.add_reflection_turn(
            st.session_state, ChatTurn(user="", assistant=intro)
        )
        st.rerun()
        return

    _render_chat(history, "Veileder")

    user_msg = st.chat_input("Del dine tanker...")

    if user_msg:
        reply = services["reflection"].run_turn(
            context=context,
            user_message=user_msg,
            session=session_state.get_agent_session(st.session_state, "reflection"),
        )
        session_state.add_reflection_turn(
            st.session_state, ChatTurn(user=user_msg, assistant=reply)
        )
        st.rerun()

    st.divider()
    if st.button("Ferdig", use_container_width=True, type="primary"):
        session_state.reset_for_new_scenario(st.session_state)
        st.rerun()


from core.game_state import SPARRING_TOPICS, SparringTopic

def render_sparring_setup() -> None:
    """Step 20 - Select a sparring topic (Endless Mode)."""
    st.subheader("🥊 Verbal Sparring (Endless Arcade)")
    st.caption("Velg et tema. Hvor lenge klarer du å holde ut?")
    
    cols = st.columns(3)
    for i, topic in enumerate(SPARRING_TOPICS):
        with cols[i]:
            with st.container(border=True):
                st.markdown(f"<div style='font-size: 40px; text-align: center;'>{topic.icon}</div>", unsafe_allow_html=True)
                st.markdown(f"<h3 style='text-align: center;'>{topic.title}</h3>", unsafe_allow_html=True)
                st.markdown(f"<p style='text-align: center; color: gray;'>{topic.description}</p>", unsafe_allow_html=True)
                
                if st.button(f"Start {topic.title}", key=f"btn_topic_{topic.id}", use_container_width=True, type="primary"):
                    # Initialize Game State for Endless Mode
                    st.session_state.game_state = GameState(
                        topic=topic,
                        level_number=1,
                        score=0,
                        level=None, # Will be generated
                        player_hp=100,
                        opponent_hp=100,
                        total_rounds=5,
                    )
                    
                    # Reset chat history
                    st.session_state.chat_history = []
                    session_state.refresh_agent_session(st.session_state, "scenario")
                    
                    st.session_state.step = 21 # Go to game
                    st.rerun()

def render_sparring_game() -> None:
    """Step 21 - The actual game loop (Endless Mode)."""
    game: GameState = st.session_state.game_state
    if not game:
        st.session_state.step = 20
        st.rerun()
        return

    # 0. Generate Level if missing
    if not game.level:
        with st.spinner(f"Genererer Nivå {game.level_number}: {game.topic.title}..."):
            game.level = services["referee"].generate_level(game.topic, game.level_number, profiler=st.session_state.profiler)
            # Reset HPs based on new level
            game.player_hp = game.level.initial_player_hp
            game.opponent_hp = game.level.initial_opponent_hp
            game.current_round = None
            game.last_round_signature = None
            game.rounds = []
            game.round_index = 0
            st.session_state.chat_history = [] # Clear history for new opponent
            st.rerun()
            return

    # Pre-generate 5 nano-scenarios to avoid per-turn latency
    if not game.rounds:
        with st.spinner(f"Laster 5 situasjoner for {game.topic.title}..."):
            game.rounds = services["referee"].generate_round_batch(game.level, count=5, profiler=st.session_state.profiler)
            game.round_index = 0
            game.current_round = game.rounds[0] if game.rounds else None
        st.rerun()
        return

    # 1. Render Header & Health
    render_fight_header(game.level.opponent_name, game.level.title, game.level.avatar_path, game.score)
    
    col_health_user, col_health_opp = st.columns(2)
    with col_health_user:
        render_health_bar("Din Utholdenhet", game.player_hp, 100, "green")
    with col_health_opp:
        render_health_bar(f"{game.level.opponent_name}s Stahet", game.opponent_hp, 100, "red")
        
    st.divider()

    # 2. Check Game Over / Level Complete
    if game.player_hp <= 0:
        st.error(f"GAME OVER! Du klarte deg til Nivå {game.level_number}.")
        if st.button("Prøv igjen", type="primary"):
            st.session_state.step = 20
            st.rerun()
        return

    # If all pre-generated rounds are played, finish immediately
    if game.round_index >= len(game.rounds) and game.rounds:
        st.balloons()
        st.success(f"Økt fullført! Du håndterte {len(game.rounds)} situasjoner.")
        if st.button("Neste nivå ➡️", type="primary"):
            game.level_number += 1
            game.score += 100
            game.level = None # Trigger generation
            game.rounds = []
            game.round_index = 0
            st.rerun()
        if st.button("Til dashboard", type="primary"):
            st.session_state.step = 1
            st.rerun()
        return

    # 3. Select current round from pre-generated list
    if not game.current_round:
        game.current_round = game.rounds[game.round_index]

    # 4. Display Round Context & Attack
    round_data = game.current_round
    
    with st.container(border=True):
        st.caption(f"Situasjon {game.round_index + 1} av {len(game.rounds)}: {round_data.context}")
        render_chat_message("assistant", round_data.attack, avatar=game.level.avatar_path)

    # 5. Display Options
    def on_option_selected(option):
        # Apply damage
        game.player_hp -= option.damage_user
        game.opponent_hp -= option.damage_opponent
        
        # Add to history
        session_state.append_chat_turn(
            st.session_state, 
            ChatTurn(user=option.text, assistant=round_data.attack)
        )
        
        # Feedback
        st.toast(f"{option.feedback} (Deg: -{option.damage_user}, {game.level.opponent_name}: -{option.damage_opponent})")

        # Advance to next prepared round without new API calls
        game.round_index += 1
        game.current_round = None
        st.rerun()

    st.write("### Velg ditt mottrekk:")
    render_round_options(round_data.options, on_option_selected, key_suffix=str(game.round_index))




def render_dashboard() -> None:
    """Step 1 - Unified Dashboard for selecting training mode."""
    st.title("Velg Treningsform")
    
    tab1, tab2 = st.tabs(["Scenario Trening", "Verbal Sparring 🥊"])
    
    with tab1:
        render_scenario_selection_step()
        
    with tab2:
        render_sparring_setup()

def check_login() -> bool:
    """Simple PIN-based login."""
    if st.session_state.get("logged_in", False):
        return True

    st.markdown(
        """
        <style>
        .stTextInput > div > div > input {
            text-align: center;
            font-size: 24px;
            letter-spacing: 5px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🔒 Adgangskontroll")
        st.caption("Vennligst skriv inn tilgangskoden for å fortsette.")
        
        code = st.text_input("Kode", type="password", label_visibility="collapsed")
        
        if code:
            # Check secrets first, then fallback to hardcoded (or environment)
            correct_code = "090794"
            try:
                if hasattr(st, "secrets") and "LOGIN_CODE" in st.secrets:
                    correct_code = st.secrets["LOGIN_CODE"]
            except Exception:
                pass  # Secrets file not found or other error

            if os.getenv("LOGIN_CODE"):
                correct_code = os.getenv("LOGIN_CODE")

            if code == correct_code:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Feil kode. Prøv igjen.")
                
    return False


def main() -> None:
    """Application entrypoint."""
    session_state.ensure_session_state(st.session_state)
    
    if "profiler" not in st.session_state:
        st.session_state.profiler = Profiler()
    
    if not check_login():
        return

    render_header()

    # Remove sidebar mode selection
    # with st.sidebar: ...

    step = st.session_state.step
    
    # Unified Flow
    content_placeholder = st.empty()
    
    with content_placeholder.container():
        if step == 1:
            render_dashboard()
        elif step == 10:
            render_custom_setup_step()
        elif step == 11:
            render_custom_picker_step()
        elif step == 2:
            render_configuration_step()
        elif step == 3:
            render_scenario_step()
        elif step == 4:
            render_feedback_step()
        elif step == 5:
            render_reflection_step()
        elif step == 20: # Legacy step, redirect to dashboard
            st.session_state.step = 1
            st.rerun()
        elif step == 21:
            render_sparring_game()
        else:
            session_state.reset_for_new_scenario(st.session_state)
            st.rerun()

    # Render debug/performance info
    if "profiler" in st.session_state:
        with st.expander("🔧 Teknisk Info & Ytelse", expanded=False):
            profiler: Profiler = st.session_state.profiler
            entries = profiler.get_entries()
            if not entries:
                st.info("Ingen målinger ennå.")
            else:
                # Show as a table
                data = []
                for e in entries:
                    duration = f"{e.duration:.2f}s" if e.duration else "Running..."
                    row = {"Operation": e.name, "Duration": duration, "Start": time.strftime("%H:%M:%S", time.localtime(e.start_time))}
                    if e.metadata:
                        row["Metadata"] = str(e.metadata)
                    data.append(row)
                st.table(data)
                
                if st.button("Nullstill målinger"):
                    profiler.clear()
                    st.rerun()


if __name__ == "__main__":
    main()
