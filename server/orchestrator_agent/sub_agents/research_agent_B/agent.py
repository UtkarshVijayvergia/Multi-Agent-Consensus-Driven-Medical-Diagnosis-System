from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
from google.genai.types import GenerateContentConfig

from .prompt import RESEARCH_AGENT_B_PROMPT_V3
from ...callbacks.conversation_memory_manager import ConversationMemoryManager
memory_manager = ConversationMemoryManager() # Create memory manager instance

import os
from dotenv import load_dotenv
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
AGENT_MODEL = os.getenv("AGENT_MODEL")


Research_Agent_B = LlmAgent(
    model=AGENT_MODEL,
    name="Research_Agent_B",
    instruction=RESEARCH_AGENT_B_PROMPT_V3,
    generate_content_config=GenerateContentConfig(
        max_output_tokens=350
    ),
    output_key="Research_Agent_B_output",
    after_model_callback=memory_manager.update_history,
)