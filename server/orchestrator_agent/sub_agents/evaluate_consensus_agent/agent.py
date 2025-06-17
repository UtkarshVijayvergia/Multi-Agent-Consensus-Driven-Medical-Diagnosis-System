from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
from google.genai.types import GenerateContentConfig

from .prompt import EVALUATE_CONSENSUS_AGENT_PROMPT_V1
from ...tools.exit_loop import exit_loop
from ...callbacks.increment_round_if_no_consensus import increment_round_if_no_consensus
from ...callbacks.conversation_memory_manager import ConversationMemoryManager
memory_manager = ConversationMemoryManager() # Create memory manager instance

import os
from dotenv import load_dotenv
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
AGENT_MODEL = os.getenv("AGENT_MODEL")


Evaluate_Consensus_Agent = LlmAgent(
    model=AGENT_MODEL,
    name="Evaluate_Consensus_Agent",
    instruction=EVALUATE_CONSENSUS_AGENT_PROMPT_V1,
    generate_content_config=GenerateContentConfig(
        max_output_tokens=100
    ),
    tools=[exit_loop],
    after_model_callback=increment_round_if_no_consensus,
)