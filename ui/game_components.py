import streamlit as st
from core.game_state import SparringOption

def render_health_bar(label: str, current: int, max_val: int, color: str = "green"):
    """Renders a visual health bar."""
    percentage = max(0, min(100, int((current / max_val) * 100)))
    
    st.markdown(f"**{label}** ({current}/{max_val})")
    st.markdown(
        f"""
        <div style="background-color: #ddd; border-radius: 10px; width: 100%; height: 20px;">
            <div style="background-color: {color}; width: {percentage}%; height: 100%; border-radius: 10px; transition: width 0.5s;"></div>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_fight_header(opponent_name: str, title: str, avatar: str, score: int = 0):
    """Renders the arcade-style fight header."""
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col1:
        st.metric("Score", score)
            
    with col2:
        st.markdown(f"<h1 style='text-align: center; margin: 0;'>{title}</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; font-size: 1.2em; color: gray;'>VS {opponent_name}</p>", unsafe_allow_html=True)

    with col3:
        # Avatar (Opponent)
        if avatar.startswith("assets/") or avatar.startswith("http"):
            st.image(avatar, width=80)
        else:
            st.markdown(f"<div style='font-size: 60px; text-align: center;'>{avatar}</div>", unsafe_allow_html=True)


def render_round_options(options: list[SparringOption], on_select: callable, key_suffix: str = ""):
    """Renders 4 large buttons for the user's move."""
    
    # Use a 2x2 grid for better mobile/desktop layout
    col1, col2 = st.columns(2)
    
    for i, option in enumerate(options):
        # Determine column
        col = col1 if i % 2 == 0 else col2
        
        with col:
            # We use a callback to pass the selected option back
            if st.button(option.text, key=f"opt_{i}_{key_suffix}", use_container_width=True, type="primary"):
                on_select(option)

def render_round_result(option: SparringOption):
    """Displays the result of the chosen move."""
    
    if option.type == "critical_hit":
        color = "green"
        icon = "🌟"
        title = "CRITICAL HIT!"
    elif option.type == "good":
        color = "lightgreen"
        icon = "✅"
        title = "Godt svar!"
    elif option.type == "weak":
        color = "orange"
        icon = "⚠️"
        title = "Svakt..."
    else: # critical_fail
        color = "red"
        icon = "💥"
        title = "AU! Den svei."

    st.markdown(
        f"""
        <div style="padding: 15px; border-radius: 10px; background-color: {color}; color: white; text-align: center; margin-top: 10px; animation: fadeIn 0.5s;">
            <h2 style="margin:0;">{icon} {title}</h2>
            <p style="font-size: 1.1em;">{option.feedback}</p>
            <p style="font-size: 0.9em; opacity: 0.9;">(Deg: -{option.damage_user}, Motstander: -{option.damage_opponent})</p>
        </div>
        """,
        unsafe_allow_html=True
    )
