"""Reusable UI components for the Motstandstrener application."""

import streamlit as st
from typing import Dict, Any, Optional

def render_header(title: str = "Motstandstrener", subtitle: str = "Pilot"):
    """Render a consistent header."""
    st.title(f"{title} :grey[{subtitle}]")
    st.markdown("---")

def render_chat_message(role: str, content: str, avatar: str = None):
    """Render a styled chat message."""
    with st.chat_message(role, avatar=avatar):
        st.markdown(content)

def render_scenario_card(
    scenario: Dict[str, Any], 
    on_click: callable, 
    key: str
):
    """Render a card for a scenario option using native Streamlit container."""
    with st.container(border=True):
        st.subheader(scenario['title'])
        st.markdown(scenario['summary'])
        st.caption(f"**Fokus:** {scenario.get('focus', 'Generelt')}")
        
        if st.button(f"Velg: {scenario['title']}", key=key, use_container_width=True, type="primary"):
            on_click()

def render_scenario_briefing(context: Any):
    """Render a clear mission briefing for the user (vertical layout)."""
    with st.container(border=True):
        st.markdown("### 📋 Oppdrag")
        st.caption("SCENARIO (AI-GENERERT)")
        st.markdown(f"**{context.scenario_title}**")
        st.markdown(context.scenario_summary)
        
        st.divider()
        
        st.caption("MOTPART")
        st.warning(context.opponent_name or "Ukjent")
        
    with st.container(border=True):
        st.markdown("### 👤 Din Kontekst")
        # st.caption("DETTE HAR DU LAGT INN") # Removed to avoid confusion for pre-built scenarios
        
        st.markdown("**Din Rolle**")
        st.info(context.role)
        
        st.markdown("**Situasjon**")
        st.markdown(context.situation)
        
        st.markdown("**Ditt Mål**")
        st.markdown(context.goal)

# def render_dynamic_indicator(params: Dict[str, float]):
#     """Removed per user request."""
#     pass

def render_scenario_selection_card(
    scenario: Any, 
    on_click: callable, 
    key: str
):
    """Render a card for selecting a pre-built scenario."""
    with st.container(border=True):
        col1, col2 = st.columns([1, 4])
        with col1:
            st.markdown(f"# {scenario.icon}")
        with col2:
            st.subheader(scenario.title)
            st.caption(scenario.summary)
        
        if st.button("Velg dette scenarioet", key=key, use_container_width=True, type="primary"):
            on_click()

def render_custom_scenario_card(on_click: callable, key: str):
    """Render a card for creating a custom scenario."""
    with st.container(border=True):
        col1, col2 = st.columns([1, 4])
        with col1:
            st.markdown("# 🛠️")
        with col2:
            st.subheader("Skreddersøm")
            st.caption("Lag ditt eget scenario fra bunnen av.")
        
        if st.button("Lag eget scenario", key=key, use_container_width=True, type="primary"):
            on_click()

def render_difficulty_selector(current_difficulty: str) -> str:
    """Render a selector for difficulty level."""
    st.markdown("### Velg vanskelighetsgrad")
    
    difficulties = {
        "Easy": "🟢 Lett (Samarbeidsvillig)",
        "Medium": "🟡 Medium (Skeptisk)",
        "Hard": "🔴 Vanskelig (Krevende)",
    }
    
    selected = st.radio(
        "Vanskelighetsgrad",
        options=["Easy", "Medium", "Hard"],
        format_func=lambda x: difficulties[x],
        index=["Easy", "Medium", "Hard"].index(current_difficulty),
        label_visibility="collapsed"
    )
    return selected

def render_context_sidebar(context: Any):
    """Render the current scenario context in the sidebar."""
    if not context:
        return
        
    st.sidebar.divider()
    st.sidebar.markdown("### Scenario")
    st.sidebar.markdown(f"**Rolle:** {context.role}")
    st.sidebar.markdown(f"**Mål:** {context.goal}")
    
    if hasattr(context, 'difficulty'):
        st.sidebar.markdown(f"**Nivå:** {context.difficulty}")
