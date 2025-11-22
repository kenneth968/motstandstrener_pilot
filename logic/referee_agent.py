"""Referee agent for the verbal sparring (arcade) mode."""

from __future__ import annotations

import json
import random
from typing import List

from core.game_state import SparringLevel, SparringRound, SparringOption, SparringTopic
from core.openai_client import AgentRegistry
from logic.game_rules import (
    calculate_initial_hp, 
    get_random_avatar, 
    is_valid_option, 
    create_fallback_level, 
    create_fallback_round, 
    create_fallback_batch
)


class RefereeAgentService:
    """Generates opponents and rounds for the sparring mini-game."""

    def __init__(self, registry: AgentRegistry, agent_name: str = "referee"):
        self.registry = registry
        self.agent_name = agent_name

    def generate_level(self, topic: SparringTopic, difficulty: int, profiler: object = None) -> SparringLevel:
        """Creates a unique level based on topic and difficulty, with guardrails."""

        player_hp, opponent_hp = calculate_initial_hp(difficulty)

        prompt = f"""
TASK: Create a level for a verbal sparring game.
**Topic**: {topic.title} ({topic.description})
**Level Difficulty**: {difficulty} (1=Easy, 10=Impossible)
**Language**: NORWEGIAN (Norsk)

**Your Job**:
Create a unique opponent and scenario.
- **Easy Levels (1-3)**: Clumsy manipulation, obvious flaws.
- **Medium Levels (4-6)**: Subtle guilt-tripping, passive-aggressive.
- **Hard Levels (7+)**: Master manipulators, narcissists, gaslighting pros.

**Output Format**:
Return ONLY a JSON object:
{{
  "opponent_name": "Name (Norwegian)",
  "opponent_role": "Role (e.g. 'Gjerrig Sjef')",
  "attack_style": "Short description of their style (in Norwegian)",
  "weakness": "What works against them? (in Norwegian)",
  "win_condition": "Goal for the player (in Norwegian)",
  "difficulty_prompt": "Instructions for the AI playing this opponent. Be specific about their tone and tactics."
}}
""".strip()

        try:
            response_text = self.registry.run(
                self.agent_name,
                prompt,
                profiler=profiler
            )

            # Clean up potential markdown code blocks
            cleaned_text = response_text.replace("```json", "").replace("```", "").strip()
            payload = json.loads(cleaned_text)
            
            return SparringLevel(
                id=f"{topic.id}_lvl_{difficulty}",
                title=f"Nivå {difficulty}: {payload.get('opponent_role', 'Motstander')}",
                opponent_name=payload.get("opponent_name", "Motstander"),
                opponent_role=payload.get("opponent_role", "Motstander"),
                attack_style=payload.get("attack_style", "Pressende og krevende"),
                weakness=payload.get("weakness", "Rolig fakta"),
                win_condition=payload.get("win_condition", "Hold roen og sett grenser"),
                difficulty_prompt=payload.get(
                    "difficulty_prompt",
                    "Vær direkte, pressende og test grensene til spilleren.",
                ),
                initial_player_hp=player_hp,
                initial_opponent_hp=opponent_hp,
                avatar_path=get_random_avatar(),
            )
        except Exception as exc:
            print(f"Level generation error: {exc}")
            return create_fallback_level(topic, difficulty)

    def generate_round(self, level: SparringLevel, history: list, profiler: object = None) -> SparringRound:
        """Generates a new round with validation and deterministic fallback."""

        history_lines = []
        for entry in history[-3:]:
            if "role" in entry and "content" in entry:
                history_lines.append(f"{entry['role']}: {entry['content']}")
            elif "user" in entry and "assistant" in entry:
                history_lines.append(f"Bruker: {entry['user']}")
                history_lines.append(f"Motstander: {entry['assistant']}")
        history_text = "\n".join(history_lines) if history_lines else "Start of conversation."

        prompt = f"""
TASK: Generate the next turn in the conversation.
**Level**: {level.title}
**Opponent**: {level.opponent_name} ({level.opponent_role})
**Style**: {level.attack_style}
**Weakness**: {level.weakness}
**Win Condition**: {level.win_condition}
**Opponent Instructions**: {level.difficulty_prompt}
**Language**: NORWEGIAN (Norsk)

**History**:
{history_text}

**Your Job**:
1. **Context**: A brief setup (e.g., "Du kommer 5 minutter for sent.").
2. **Attack**: The opponent's line (Gaslighting/Manipulation).
3. **4 Options**: Distinct responses for the user.
   - **Critical Fail**: Defensive, apologetic, or aggressive (User takes 20-30 dmg).
   - **Weak**: Passive or vague (User takes 10-15 dmg).
   - **Good**: Clear boundary or fact-check (Opponent takes 10-15 dmg).
   - **Critical Hit**: Perfect counter using the specific weakness (Opponent takes 20-30 dmg).

**Output Format**:
Return ONLY a JSON object:
{{
  "context": "...",
  "attack": "...",
  "options": [
    {{ "text": "...", "damage_user": 30, "damage_opponent": 0, "feedback": "Ikke unnskyld deg!", "type": "critical_fail" }},
    {{ "text": "...", "damage_user": 10, "damage_opponent": 0, "feedback": "For passivt.", "type": "weak" }},
    {{ "text": "...", "damage_user": 0, "damage_opponent": 15, "feedback": "God grensesetting.", "type": "good" }},
    {{ "text": "...", "damage_user": 0, "damage_opponent": 30, "feedback": "Perfekt treff!", "type": "critical_hit" }}
  ]
}}
""".strip()

        try:
            response_text = self.registry.run(
                self.agent_name,
                prompt,
                profiler=profiler
            )
            
            cleaned_text = response_text.replace("```json", "").replace("```", "").strip()
            data = json.loads(cleaned_text)
            
            options = [SparringOption(**opt) for opt in data.get("options", []) if is_valid_option(opt)]
            if len(options) != 4:
                raise ValueError("Expected 4 valid options")

            random.shuffle(options)
            return SparringRound(
                context=data.get("context", "Motstanderen vil teste deg videre."),
                attack=data.get("attack", "Dette holder ikke — hva tenker du egentlig?"),
                options=options,
            )
        except Exception as exc:
            print(f"Referee error: {exc}")
            return create_fallback_round(level)

    def generate_round_batch(self, level: SparringLevel, count: int = 5, profiler: object = None) -> List[SparringRound]:
        """Generate a batch of nano-scenarios to avoid per-turn latency."""

        prompt = f"""
TASK: Generate {count} DIFFERENT nano-scenarios under the same topic.
Each round must have a distinct setting that still fits the topic (e.g. familieselskap, jobb-lunsj, treningssenter, chat/gruppe, taxi).
Each context should be 2-3 short sentences that set the scene before the attack.
Keep them concise and self-contained: one vivid setup + one attack + 4 responses.

**Opponent**: {level.opponent_name} ({level.opponent_role})
**Style**: {level.attack_style}
**Weakness**: {level.weakness}
**Win Condition**: {level.win_condition}
**Instructions**: {level.difficulty_prompt}
**Language**: NORWEGIAN (Norsk)

Output ONLY a single JSON object containing an array of rounds:
{{
  "rounds": [
    {{
      "context": "... (2-3 setninger, hvor/hvordan skjer det nå?)",
      "attack": "... (setningen som triggere et svar)",
      "options": [
        {{ "text": "...", "damage_user": 25, "damage_opponent": 0, "feedback": "...", "type": "critical_fail" }},
        {{ "text": "...", "damage_user": 12, "damage_opponent": 0, "feedback": "...", "type": "weak" }},
        {{ "text": "...", "damage_user": 0, "damage_opponent": 12, "feedback": "...", "type": "good" }},
        {{ "text": "...", "damage_user": 0, "damage_opponent": 25, "feedback": "...", "type": "critical_hit" }}
      ]
    }}
  ]
}}
Rules: vary the setting each round, stay on topic, keep it short, no English.
Ensure the output is valid JSON.
""".strip()

        try:
            response_text = self.registry.run(
                self.agent_name,
                prompt,
                profiler=profiler
            )
            
            cleaned_text = response_text.replace("```json", "").replace("```", "").strip()
            data = json.loads(cleaned_text)
            
            rounds_raw = data.get("rounds", [])
            parsed: List[SparringRound] = []
            for item in rounds_raw:
                options = [
                    SparringOption(**opt)
                    for opt in item.get("options", [])
                    if is_valid_option(opt)
                ]
                if len(options) != 4:
                    continue
                random.shuffle(options)
                parsed.append(
                    SparringRound(
                        context=item.get("context", "Uklart sted"),
                        attack=item.get("attack", "Jeg er uenig, hvorfor insisterer du?"),
                        options=options,
                    )
                )
                if len(parsed) >= count:
                    break

            if parsed:
                return parsed
        except Exception as exc:
            print(f"Referee batch error: {exc}")

        # Fallback: generate different offline contexts under same topic
        return create_fallback_batch(level, count)
