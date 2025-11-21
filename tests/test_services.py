import unittest

from core.game_state import SparringLevel, SparringTopic
from core.state import ScenarioContext
from logic.scenario_agent import _build_base_prompt
from logic.scenario_planner import ScenarioPlannerService
from logic.referee_agent import RefereeAgentService


class DummyRegistry:
    def run(self, *_args, **_kwargs):
        return ""


class FailingCompletions:
    @staticmethod
    def create(**_kwargs):
        raise RuntimeError("fail")


class FailingChat:
    completions = FailingCompletions()


class FailingClient:
    chat = FailingChat()


class ServicesTests(unittest.TestCase):
    def test_planner_parse_valid_payload(self):
        payload = """
        {
          "scenarios": [
            {
              "id": "abc",
              "title": "Tittel",
              "summary": "Kort tekst",
              "focus": "Grenser",
              "agent_instructions": "Vær krevende",
              "opponent_name": "Reidar"
            }
          ]
        }
        """
        options = ScenarioPlannerService._parse_options(payload)
        self.assertEqual(len(options), 1)
        self.assertEqual(options[0]["id"], "abc")
        self.assertEqual(options[0]["opponent_name"], "Reidar")

    def test_planner_parse_with_noise(self):
        payload = "noisy header {\"scenarios\": [{\"id\": \"x\", \"title\": \"Y\", \"summary\": \"Z\", \"agent_instructions\": \"Test\"}]} trailer"
        options = ScenarioPlannerService._parse_options(payload)
        self.assertEqual(len(options), 1)
        self.assertEqual(options[0]["id"], "x")

    def test_build_base_prompt_contains_difficulty_and_goal(self):
        context = ScenarioContext(
            role="Teamleder",
            situation="Utfordrende 1:1",
            goal="Bli tydeligere",
            scenario_title="Den Stille",
            scenario_summary="Kort",
            agent_instructions="Vær kort",
            opponent_name="Ingrid",
            difficulty="Hard",
        )
        prompt = _build_base_prompt(context, {"resilience": 0.5, "clarity": 0.5, "empathy": 0.5})
        self.assertIn("Hard", prompt)
        self.assertIn(context.goal, prompt)
        self.assertIn(context.opponent_name, prompt)

    def test_referee_fallback_on_failure(self):
        # Fail both level and round generation to assert stable fallbacks
        referee = RefereeAgentService(FailingClient(), model="dummy")

        topic = SparringTopic(id="t", title="Test", description="Desc", icon="💥")
        level = referee.generate_level(topic, difficulty=5)
        self.assertIsInstance(level, SparringLevel)
        self.assertEqual(level.opponent_name, "Test")

        round_data = referee.generate_round(level, history=[])
        self.assertEqual(len(round_data.options), 4)
        types = {opt.type for opt in round_data.options}
        self.assertEqual(types, {"critical_fail", "weak", "good", "critical_hit"})

        batch = referee.generate_round_batch(level, count=5)
        self.assertEqual(len(batch), 5)
        for rnd in batch:
            self.assertEqual(len(rnd.options), 4)


if __name__ == "__main__":
    unittest.main()
