"""Referee agent for the verbal sparring (arcade) mode."""

from __future__ import annotations

import json
import random
from typing import List

from core.game_state import SparringLevel, SparringRound, SparringOption, SparringTopic

# Simple emoji avatars; replace with asset paths later if desired.
AVATAR_POOL: List[str] = ["💥", "😠", "😤", "😑", "😏", "🧊", "🧠", "🦊", "🪨", "🔥"]


class RefereeAgentService:
    """Generates opponents and rounds for the sparring mini-game."""

    def __init__(self, client, model: str):
        self.client = client
        self.model = model

    def generate_level(self, topic: SparringTopic, difficulty: int, profiler: object = None) -> SparringLevel:
        """Creates a unique level based on topic and difficulty, with guardrails."""

        player_hp = 100
        opponent_hp = 100

        if difficulty >= 4:
            opponent_hp = 120  # Harder opponents have more stamina
        if difficulty >= 7:
            player_hp = 80  # You start tired/stressed

        system_prompt = f"""
You are a Game Designer creating a level for a verbal sparring game.
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
            if profiler:
                with profiler.profile("Referee: Generate Level") as p_entry:
                    try:
                        response = self.client.chat.completions.create(
                            model=self.model,
                            messages=[{"role": "system", "content": system_prompt}],
                            response_format={"type": "json_object"},
                        )
                    except Exception as exc:
                        p_entry.metadata["error"] = str(exc)
                        raise exc
            else:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "system", "content": system_prompt}],
                    response_format={"type": "json_object"},
                )

            payload = json.loads(response.choices[0].message.content)
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
                avatar_path=random.choice(AVATAR_POOL),
            )
        except Exception as exc:
            print(f"Level generation error: {exc}")
            # Offline fallback: use topic info to keep immersion
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

    def generate_round(self, level: SparringLevel, history: list, profiler: object = None) -> SparringRound:
        """Generates a new round with validation and deterministic fallback."""

        system_prompt = f"""
You are the GAME MASTER for a verbal sparring match.
**Level**: {level.title}
**Opponent**: {level.opponent_name} ({level.opponent_role})
**Style**: {level.attack_style}
**Weakness**: {level.weakness}
**Win Condition**: {level.win_condition}
**Opponent Instructions**: {level.difficulty_prompt}
**Language**: NORWEGIAN (Norsk)

**Your Job**:
Generate the next turn in the conversation.
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

        history_lines = []
        for entry in history[-3:]:
            if "role" in entry and "content" in entry:
                history_lines.append(f"{entry['role']}: {entry['content']}")
            elif "user" in entry and "assistant" in entry:
                history_lines.append(f"Bruker: {entry['user']}")
                history_lines.append(f"Motstander: {entry['assistant']}")
        history_text = "\n".join(history_lines) if history_lines else "Start of conversation."

        user_prompt = f"**History**:\n{history_text}\n\nGenerate the next round."

        try:
            if profiler:
                with profiler.profile("Referee: Generate Round") as p_entry:
                    try:
                        response = self.client.chat.completions.create(
                            model=self.model,
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt},
                            ],
                            response_format={"type": "json_object"},
                        )
                    except Exception as exc:
                        p_entry.metadata["error"] = str(exc)
                        raise exc
            else:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    response_format={"type": "json_object"},
                )

            data = json.loads(response.choices[0].message.content)
            options = [SparringOption(**opt) for opt in data.get("options", []) if self._is_valid_option(opt)]
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
            return self._fallback_round(level)

    def generate_round_batch(self, level: SparringLevel, count: int = 5, profiler: object = None) -> List[SparringRound]:
        """Generate a batch of nano-scenarios to avoid per-turn latency."""

        system_prompt = f"""
You are the GAME MASTER for a verbal sparring match.
Generate {count} DIFFERENT nano-scenarios under the same topic.
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
            if profiler:
                with profiler.profile("Referee: Generate Batch") as p_entry:
                    try:
                        response = self.client.chat.completions.create(
                            model=self.model,
                            messages=[{"role": "system", "content": system_prompt}],
                            response_format={"type": "json_object"},
                        )
                    except Exception as exc:
                        p_entry.metadata["error"] = str(exc)
                        raise exc
            else:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "system", "content": system_prompt}],
                    response_format={"type": "json_object"},
                )
            data = json.loads(response.choices[0].message.content)
            rounds_raw = data.get("rounds", [])
            parsed: List[SparringRound] = []
            for item in rounds_raw:
                options = [
                    SparringOption(**opt)
                    for opt in item.get("options", [])
                    if self._is_valid_option(opt)
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
        return self._fallback_batch(level, count)

    @staticmethod
    def _is_valid_option(option: dict) -> bool:
        required = {"text", "damage_user", "damage_opponent", "feedback", "type"}
        return isinstance(option, dict) and required <= set(option.keys())

    @staticmethod
    def _fallback_round(level: SparringLevel) -> SparringRound:
        """Deterministic offline fallback to keep the UI responsive."""

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

    @classmethod
    def _fallback_batch(cls, level: SparringLevel, count: int) -> List[SparringRound]:
        contexts = [
            "Familiebesøk: onkel tar ordet ved middagsbordet, alle lytter mens han gjør et poeng ut av politikken.",
            "Kantina på jobb: kollega kommenterer høyt mens flere rundt dere følger med.",
            "Treningssenteret: en bekjent starter småprat og vil fortelle deg hvordan ting bør gjøres.",
            "Chatgruppe: noen kaster inn en spiss kommentar og forventer svar fra deg.",
            "Taxi-kø: en fremmed vil diskutere temaet og presser på mens dere venter.",
        ]
        rounds: List[SparringRound] = []
        for i in range(count):
            base = cls._fallback_round(level)
            rounds.append(
                SparringRound(
                    context=contexts[i % len(contexts)],
                    attack=base.attack,
                    options=base.options,
                )
            )
        return rounds
