from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class SparringLevel:
    id: str
    title: str
    opponent_name: str
    opponent_role: str
    attack_style: str
    weakness: str
    win_condition: str
    difficulty_prompt: str # Specific instructions for the opponent agent
    initial_opponent_hp: int = 100
    initial_player_hp: int = 100
    avatar_path: str = "assets/avatars/reidar.png" # Default placeholder

@dataclass
class SparringOption:
    text: str
    damage_user: int
    damage_opponent: int
    feedback: str
    type: str # "critical_fail", "weak", "good", "critical_hit"

@dataclass
class SparringRound:
    context: str # "Jonas is late..."
    attack: str # "I never said 2 PM!"
    options: List[SparringOption]

@dataclass
class SparringTopic:
    id: str
    title: str
    description: str
    icon: str

@dataclass
class GameState:
    topic: SparringTopic
    level_number: int
    score: int
    level: SparringLevel # The current active level details
    player_hp: int
    opponent_hp: int
    turn_count: int = 0
    history: List[dict] = field(default_factory=list)
    is_game_over: bool = False
    game_result: Optional[str] = None # "win" or "loss"
    current_round: Optional[SparringRound] = None
    last_round_signature: Optional[str] = None
    rounds: List[SparringRound] = field(default_factory=list)
    round_index: int = 0
    total_rounds: int = 5

# Define the Gaslighting Ladder
GASLIGHTING_LEVELS = [
    SparringLevel(
        id="gaslight_1",
        title="Nivå 1: Den Glemske Vennen",
        opponent_name="Jonas",
        opponent_role="Venn",
        attack_style="Benekter fakta ('Jeg sa aldri det')",
        weakness="Rolig gjentakelse av fakta",
        win_condition="Få Jonas til å innrømme usikkerhet eller trekke seg.",
        difficulty_prompt="Du er Jonas. Du har glemt en avtale, men nekter for at dere hadde en. Si ting som 'Hva? Det har vi aldri snakket om' eller 'Du husker feil'. Vær forvirret, ikke aggressiv.",
        avatar_path="assets/avatars/leif.png" # Reuse Leif (sad/pathetic fits somewhat)
    ),
    SparringLevel(
        id="gaslight_2",
        title="Nivå 2: Offeret",
        opponent_name="Silje",
        opponent_role="Kjæreste",
        attack_style="Spiller offer ('Du er så følsom')",
        weakness="Ikke ta på deg skyld, hold fokus på saken",
        win_condition="Få Silje til å akseptere at hennes oppførsel såret deg, uten at du sier unnskyld.",
        difficulty_prompt="Du er Silje. Når brukeren konfronterer deg, bli lei deg. Si 'Herregud, du er så følsom', 'Jeg tullet bare', 'Hvorfor må du alltid lage drama?'.",
        avatar_path="assets/avatars/ingrid.png" # Reuse Ingrid (passive/neutral)
    ),
    SparringLevel(
        id="gaslight_3",
        title="Nivå 3: Virkelighetsvrideren (BOSS)",
        opponent_name="Erik",
        opponent_role="Sjef",
        attack_style="Aggressiv benektelse og motangrep",
        weakness="Gråsteinsmetoden (Grey Rocking) - kjedelig, kort, saklig",
        win_condition="Avslutt samtalen uten å bli emosjonell eller gi etter.",
        difficulty_prompt="Du er Erik, en narsissistisk sjef. Du har gjort en feil, men skylder på brukeren. Vær arrogant. 'Dette er din feil', 'Du er inkompetent', 'Jeg husker nøyaktig hva som skjedde, og du lyver'.",
        avatar_path="assets/avatars/reidar.png" # Reuse Reidar (angry)
    )
]

# Define Endless Topics
SPARRING_TOPICS = [
    SparringTopic(
        id="politisk_bedreviter",
        title="Politisk Bedreviter",
        description="Onkel ved middagsbordet som vet best om alt.",
        icon="🗣️"
    ),
    SparringTopic(
        id="kantine_kommentator",
        title="Kantine-kommentator",
        description="Kollega som alltid overprøver meningene dine i lunsjen.",
        icon="🍽️"
    ),
    SparringTopic(
        id="gym_guru",
        title="Gym-guru",
        description="Treningsbekjent som belærer deg om alt mulig.",
        icon="🏋️"
    )
]
