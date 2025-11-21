1. Konseptskisse
------------------

**Arbeidstittel:** AI-drevet scenariobasert motstandstrener (resilience-trener)

**Mål:** Hjelpe ledere, prosessledere og andre som håndterer krevende situasjoner med å øve på motstand i en trygg, lavrisiko setting. Systemet guider brukeren til innsikt og selvhjelp – ikke fasitsvar.

### De fire delene
1. **Forberedelse / kontekst** – brukeren beskriver rolle, situasjon og læringsmål. Systemet foreslår nå automatisk tre scenario-varianter (generert av en egen “scenario-planner”-agent) basert på teksten, inkludert anbefalt agentstil for motparten.
2. **Scenariochat med motstand** – brukeren velger ett av forslagene og starter chatten. AI spiller motparten (kollega, leder, gruppe) med scenario-spesifikke instruksjoner og gir realistisk motstand. Brukeren kan avslutte når som helst.
3. **Kort tilbakemelding** – 3–5 punkter om hva som fungerte, mulige alternative strategier og ett konkret tips til neste økt.
4. **Refleksjon (valgfritt)** – en rolig veiledning med spørsmålsbasert refleksjon for å omsette opplevelsen til læring.

Tone gjennom hele løypen: saklig, støttende, nysgjerrig og tydelig, aldri dømmende.

2. Teknisk plan – Python / Streamlit / Agents SDK
-------------------------------------------------

### 2.1 Mappestruktur (gjeldende)
```
motstandstrener/
├─ .venv/                 # Virtuelt miljø
├─ .env                   # API-nøkkel (aldri i Git)
├─ .gitignore             # Bl.a. sessions.db, .venv
├─ requirements.txt       # streamlit, python-dotenv, openai, openai-agents
├─ app.py                 # Streamlit entrypoint
├─ core/
│  ├─ config.py           # Laster .env og modeller
│  ├─ openai_client.py    # AgentRegistry/AgentConfig (Agents SDK)
│  ├─ sessions.py         # SQLiteSession-håndtering
│  ├─ state.py            # Session state + læringsparametre + agent-sesjoner
│  └─ learning_params.py  # Eksperiment-modul for læringsvektor
├─ logic/
│  ├─ scenario_agent.py   # Scenario-agent
│  ├─ feedback_agent.py   # Tilbakemelding-agent
│  └─ reflection_agent.py # Refleksjons-agent
└─ ui/
   └─ (placeholder for layout/components ved videreutvikling)
```

### 2.2 Oppsett (venv + pakker)
```powershell
mkdir motstandstrener
cd motstandstrener
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install streamlit python-dotenv openai openai-agents
pip freeze > requirements.txt
```
`.env` i rot: `OPENAI_API_KEY=sk-...`

### 2.3 Viktige komponenter
- **core/config.py** – laster konfig og modeller (scenario/feedback/reflection/planner).
- **core/openai_client.py** – `AgentRegistry` som oppretter `agents.Agent`, håndterer handoffs senere og kjører `Runner` via `asyncio`.
- **core/state.py** – all Streamlit-session-state inkl. scenario-kontekst, historikk, læringsparametre, scenario-forslag og agent-sesjoner.
- **core/sessions.py** – lager pseudonyme `SQLiteSession`-objekter per agent og sørger for sletting/ny ID ved reset (lagres i lokal `sessions.db`).
- **logic/** – tjenester for scenario-planning, scenario-chat, feedback og refleksjon; alle gjenbruker `AgentRegistry`.
- **app.py** – strømlinjeformet Streamlit-orkestrering av forberedelse → scenariovelger → scenariochat → tilbakemelding → refleksjon.

### 2.4 Agents SDK og handoffs
- Vi bruker `openai-agents` sitt API med `Agent`, `Runner.run_sync` og `SQLiteSession`.
- Scenario-, feedback- og refleksjonsagentene defineres med egne modeller/instruksjoner og kan senere utvides med `handoffs` (f.eks. triage-agent som velger språk/nivå).
- Runner håndterer verktøybruk/autonome avgjørelser, men vi holder første versjon enkel: tekst inn/ut + session memory.

3. Dagens MVP (Streamlit-app)
-----------------------------

1. **Forberedelse** – `render_preparation_step()` viser skjema + PII-advarsel og har ferdigutfylte eksempelverdier for rask testing.
2. **Scenariovelger** – `ScenarioPlannerService.generate_options()` (Agents SDK) lager tre strukturerte forslag med tittel, sammendrag, fokus og agent-instruksjoner. UI viser kortene og lar brukeren starte scenarioet direkte.
3. **Scenariochat** – `ScenarioAgentService.run_turn()` bygger prompt med kontekst, læringsprofil (p1–p5) og scenario-spesifikke instrukser fra planleggeren, og bruker `AgentRegistry.run(..., session=scenario_session)`. Historikken i UI bruker `st.chat_message`/`st.chat_input` mens `SQLiteSession` ivaretar AI-minnet.
4. **Tilbakemelding** – første gang steg 4 lastes kalles `FeedbackAgentService.generate()` med chat-historikk og egen sesjon, slik at output i `st.session_state.feedback` er deterministisk for resten av økten.
5. **Refleksjon (valgfritt)** – når brukeren velger å reflektere, nullstilles refleksjonssesionen og `ReflectionAgentService.run_turn()` tar over chatten med samme UI-mønster som scenario.

Øvrige detaljer:
- **Learning params** (`core/learning_params.py`) oppdateres på hver chat-turn og injiseres i scenario-prompten for enkel personalisering.
- **Reset**-knapper (avslutt scenario, avslutt refleksjon, “Start nytt scenario”) kaller `state.reset_for_new_scenario` som igjen nullstiller Streamlit state og alle `SQLiteSession`-objektene (slettet historikk + ny UUID).
- **requirements.txt** inkluderer `openai-agents` slik at installasjonen matcher koden.

4. Sessions og minnestrategi (GDPR / AI Act)
-------------------------------------------

Valgt strategi: **en `SQLiteSession` per agent (scenario, feedback, refleksjon) lagret i `sessions.db` på brukerens maskin.**

**Hvorfor:**
- All samtalehistorikk holdes lokalt, uten sky-lagring eller backend – reduserer personvernrisiko i pilotfasen.
- `sessions.db` er lagt til i `.gitignore`, slik at data aldri pushes til repo.
- Hver sesjon får en pseudonym ID (`<agent>-<uuid4()>`) gjennom `core/sessions.py`. Ingen navn/e-post/kunde-ID brukes, så data kan ikke kobles til personer uten separat mapping (som vi ikke oppretter).
- `refresh_agent_session(...)` og `reset_session_store(...)` kjører `session.clear_session()` før de genererer ny ID. Resultat: det finnes ikke gamle dialoger i databasen når en økt avsluttes.
- UI minner brukeren om å unngå persondata og gir “Start nytt scenario” / “Avslutt refleksjon” for eksplisitt sletting.

**Hvordan:**
- `core/sessions.py` kapsler `SQLiteSession` + sletting via `asyncio.run(session.clear_session())`.
- `core/state.py` holder `agent_sessions` og scenario-forslag i `st.session_state` og eksponerer `get_agent_session()` / `refresh_agent_session()`.
- `app.py` kaller `refresh_agent_session` når et scenario starter, før feedback genereres og når refleksjon trigges. Alle `AgentRegistry.run(...)`-kall får riktig session.
- Dokumenterte fordeler i dette notatet og README for å vise vurderingene opp mot GDPR/AI Act (dataminimering, slettbarhet, transparens).

5. Fremtidig læringsvektor (eksperiment)
---------------------------------------

Målet er en liten personlig “læringsprofil” som hentes og justeres per scenario. Nåværende implementasjon:
```python
def init_params():
    return {"p1": 0.5, "p2": 0.5, "p3": 0.5, "p4": 0.5, "p5": 0.5}

def update_params(params, chat_history):
    new_params = params.copy()
    n_turns = len(chat_history)
    if n_turns < 3:
        new_params["p2"] = max(0.0, params["p2"] - 0.05)
    else:
        new_params["p2"] = min(1.0, params["p2"] + 0.05)
    return new_params
```
Videre idéer:
- La p1..p5 beskrive f.eks. harmoni vs. konfrontasjon, toleranse for motstand, grad av utforskende spørsmål osv.
- Lagre vektoren i session state nå, senere i database for tilbakevendende brukere.
- Injiser verdiene i scenario-agentens prompt slik at motstand og tempo justeres automatisk.

6. Personvern / AI Act – sjekkliste for piloten
----------------------------------------------

- **Dataminimering:** Oppfordrer til å anonymisere scenarioer, lagrer kun fritekst lokalt og sletter når økten avsluttes.
- **Transparens:** UI forklarer at verktøyet er et læringsverktøy, ikke terapi/diagnostikk. Tilbakemeldinger er støtte, ikke fasit.
- **Tilgjengelig sletting:** “Start nytt scenario” og “Avslutt refleksjon” fjerner både Streamlit state og `SQLiteSession`-innhold.
- **Forståelige parametre:** Når læringsvektoren eksponeres for brukeren, må vi forklare hva tallene betyr og tilby reset.
- **Videre steg før produksjon:** Databehandleravtale, ROS/DPIA, vurdering mot AI-forordningens risikoklasser, logging/støtte dersom agentene får tilgang til flere systemer.

7. Stegvis plan mot neste MVP-iterasjon
---------------------------------------

1. **Stabilisere agentene:** legge til enkle enhetstester for `ScenarioAgentService`, `FeedbackAgentService` og `ReflectionAgentService` (mocke registry), og bekrefte at `Runner.run_sync` kalles riktig.
2. **UI-modularisering:** flytte seksjoner til `ui/layout.py` og bygge små komponenter (kort for scenariokontekst, chat-bobler) for enklere styling senere.
3. **Logging & metrics:** samle ikke-personidentifiserbare tall (antall turns, avslutningsårsak) i session state eller egen modul, slik at læringsvektor og videre innsikt får data.
4. **Refleksjonsscript:** lage en spørsmålsbank som reflection-agenten kan bruke (via tool eller strenger), så den varierer spørsmål.
5. **Ekstern deling:** skrive README med kjørebeskrivelse, personvern-notat, skjermbilder og forslag til test-scenarier, slik at pilotbrukere hos NAV eller samarbeidspartnere kan onboardes raskt.
