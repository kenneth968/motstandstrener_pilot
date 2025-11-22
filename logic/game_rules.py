"""Game rules and logic for the verbal sparring mode."""

import random
from typing import List
from core.game_state import SparringLevel, SparringRound, SparringOption, SparringTopic

# Simple emoji avatars
AVATAR_POOL: List[str] = ["💥", "😠", "😤", "😑", "😏", "🧊", "🧠", "🦊", "🪨", "🔥"]

def calculate_initial_hp(difficulty: int) -> tuple[int, int]:
    """Calculate initial HP for player and opponent based on difficulty."""
    player_hp = 100
    opponent_hp = 100

    if difficulty >= 4:
        opponent_hp = 120  # Harder opponents have more stamina
    if difficulty >= 7:
        player_hp = 80  # You start tired/stressed
        
    return player_hp, opponent_hp

def get_random_avatar() -> str:
    return random.choice(AVATAR_POOL)

def is_valid_option(option: dict) -> bool:
    """Validate that an option dictionary has all required fields."""
    required = {"text", "damage_user", "damage_opponent", "feedback", "type"}
    return isinstance(option, dict) and required <= set(option.keys())

def create_fallback_level(topic: SparringTopic, difficulty: int) -> SparringLevel:
    """Create a deterministic fallback level if generation fails."""
    player_hp, opponent_hp = calculate_initial_hp(difficulty)
    fallback_opponent = topic.title or "Motstander"
    fallback_role = topic.description or "Motstander"
    
    return SparringLevel(
        id="fallback",
        title=f"Nivå {difficulty}: {fallback_opponent}",
        opponent_name=fallback_opponent,
        opponent_role=fallback_role,
        attack_style="Belærende og pressende",
        weakness="Rolig fakta og grensesetting",
        win_condition="Hold deg saklig og avslutt på dine premisser",
        difficulty_prompt="Vær pågående og overbevist om at du har rett, men uten å bli aggressiv.",
        initial_player_hp=player_hp,
        initial_opponent_hp=opponent_hp,
        avatar_path="🤖",
    )

def create_fallback_round(level: SparringLevel) -> SparringRound:
    """Create a deterministic fallback round."""
    options = [
        SparringOption(
            text="Ok, kanskje du har rett, jeg dropper det.",
            damage_user=25,
            damage_opponent=0,
            feedback="Du ga opp for lett.",
            type="critical_fail",
        ),
        SparringOption(
            text="La oss ta dette senere.",
            damage_user=12,
            damage_opponent=0,
            feedback="Uklart og forsinkende.",
            type="weak",
        ),
        SparringOption(
            text="Jeg hører deg, men faktum er at vi avtalte dette.",
            damage_user=0,
            damage_opponent=12,
            feedback="Tydelig grensesetting.",
            type="good",
        ),
        SparringOption(
            text="Jeg forholder meg til avtalen: vi gjør det slik, punktum.",
            damage_user=0,
            damage_opponent=24,
            feedback="Presist og stødig.",
            type="critical_hit",
        ),
    ]

    random.shuffle(options)
    return SparringRound(
        context=(
            "Systemgenerert runde: en pågående samtalepartner utfordrer deg. "
            "Du er i en hverdagssituasjon og merker at motparten presser agendaen sin."
        ),
        attack=f"{level.opponent_name}: 'Dette henger ikke på greip, hvorfor presser du dette?'",
        options=options,
    )

def create_fallback_batch(level: SparringLevel, count: int) -> List[SparringRound]:
    """Create a batch of fallback rounds."""
    contexts = [
        "Familiebesøk: onkel tar ordet ved middagsbordet, alle lytter mens han gjør et poeng ut av politikken.",
        "Kantina på jobb: kollega kommenterer høyt mens flere rundt dere følger med.",
        "Treningssenteret: en bekjent starter småprat og vil fortelle deg hvordan ting bør gjøres.",
        "Chatgruppe: noen kaster inn en spiss kommentar og forventer svar fra deg.",
        "Taxi-kø: en fremmed vil diskutere temaet og presser på mens dere venter.",
    ]
    rounds: List[SparringRound] = []
    for i in range(count):
        base = create_fallback_round(level)
        rounds.append(
            SparringRound(
                context=contexts[i % len(contexts)],
                attack=base.attack,
                options=base.options,
            )
        )
    return rounds
