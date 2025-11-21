"""Defines the data structure and content for pre-built scenarios."""

from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Scenario:
    id: str
    title: str
    summary: str
    role: str
    situation: str
    goal: str
    difficulty_modifier: str  # Instructions for the agent specific to this scenario's difficulty
    opponent_name: str # Fixed opponent name for pre-built scenarios
    icon: str = "📝"
    avatar_path: Optional[str] = None

PREBUILT_SCENARIOS: List[Scenario] = [
    Scenario(
        id="steamroller",
        title="Dampveivalsen",
        summary="En kollega som avbryter og overkjører deg i møter.",
        role="Prosjektmedarbeider",
        situation="Du sitter i et planleggingsmøte. Hver gang du prøver å legge frem ditt forslag, avbryter 'Reidar' deg med sine egne meninger og nekter å slippe deg til.",
        goal="Få lagt frem forslaget ditt fullt ut og marker at du ikke vil bli avbrutt, uten å bli aggressiv.",
        difficulty_modifier="Du er utålmodig og høylytt. Avbryt brukeren hvis de nøler. Vær overbevist om at din løsning er best.",
        opponent_name="Reidar",
        icon="😤",
        avatar_path="assets/avatars/reidar.png"
    ),
    Scenario(
        id="silent_wall",
        title="Den stille veggen",
        summary="En medarbeider som ikke gir respons eller tar initiativ.",
        role="Teamleder",
        situation="Du har et oppfølgingsmøte med 'Ingrid'. Hun leverer greit, men sier ingenting i møter og virker uengasjert. Du trenger at hun tar mer eierskap.",
        goal="Få Ingrid til å åpne seg om hva hun tenker, og få en konkret forpliktelse til å bidra mer muntlig.",
        difficulty_modifier="Vær unnvikende. Svar med enstavelsesord ('ja', 'nei', 'vet ikke'). Vær passiv, men ikke fiendtlig. La brukeren jobbe for å få deg i tale.",
        opponent_name="Ingrid",
        icon="😶",
        avatar_path="assets/avatars/ingrid.png"
    ),
    Scenario(
        id="guilt_tripper",
        title="Samvittighetsfangen",
        summary="En nabo/venn som bruker skyldfølelse for å få viljen sin.",
        role="Nabo",
        situation="Naboen 'Leif' ber deg vanne plantene hans i ferien for tredje gang i år. Det passer veldig dårlig for deg denne uken.",
        goal="Si nei på en vennlig men bestemt måte, uten å la deg manipulere av hans 'stakkars meg'-historier.",
        difficulty_modifier="Spill offeret. Bruk fraser som 'Jeg trodde vi var venner', 'Jeg har ingen andre', og 'Det er typisk at jeg alltid blir sittende alene med problemene'.",
        opponent_name="Leif",
        icon="🥺",
        avatar_path="assets/avatars/leif.png"
    )
]
