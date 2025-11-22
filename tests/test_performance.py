import time
import os
import sys
from dotenv import load_dotenv
from openai import OpenAI

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.config import load_settings
from core.game_state import SparringTopic
from logic.referee_agent import RefereeAgentService
from core.profiler import Profiler

def test_performance():
    with open("tests/perf_result.txt", "w", encoding="utf-8") as f:
        def log(msg):
            print(msg)
            f.write(msg + "\n")
            
        log("Loading settings...")
        load_dotenv()
        settings = load_settings()
        
        log(f"Using Referee Model: {settings.openai.referee_agent_model}")
        
        client = OpenAI(api_key=settings.openai.api_key)
        referee = RefereeAgentService(client, settings.openai.referee_agent_model)
        profiler = Profiler()
        
        topic = SparringTopic(
            id="test_topic",
            title="Test Topic",
            description="A test topic for performance benchmarking.",
            icon="🧪"
        )
        
        log("\n--- Testing Generate Level ---")
        start_time = time.time()
        level = referee.generate_level(topic, difficulty=1, profiler=profiler)
        end_time = time.time()
        duration = end_time - start_time
        log(f"Level generated in {duration:.2f}s")
        
        if duration > 10:
            log("WARNING: Level generation took longer than 10s!")
        
        log("\n--- Testing Generate Round Batch ---")
        start_time = time.time()
        rounds = referee.generate_round_batch(level, count=5, profiler=profiler)
        end_time = time.time()
        duration = end_time - start_time
        log(f"Batch generated in {duration:.2f}s")
        
        if duration > 20:
            log("WARNING: Batch generation took longer than 20s!")

if __name__ == "__main__":
    test_performance()
