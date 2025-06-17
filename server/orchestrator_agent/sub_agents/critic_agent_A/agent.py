from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
from google.genai.types import GenerateContentConfig

from .prompt import CRITIC_AGENT_A_PROMPT_V2
from ...callbacks.conversation_memory_manager import ConversationMemoryManager
memory_manager = ConversationMemoryManager() # Create memory manager instance

import os
from dotenv import load_dotenv
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
AGENT_MODEL = os.getenv("AGENT_MODEL")


Critic_Agent_A = LlmAgent(
    model=AGENT_MODEL,
    name="Critic_Agent_A",
    instruction=CRITIC_AGENT_A_PROMPT_V2,
    generate_content_config=GenerateContentConfig(
        max_output_tokens=350
    ),
    output_key="Critic_Agent_A_output",
    after_model_callback=memory_manager.update_history,
)