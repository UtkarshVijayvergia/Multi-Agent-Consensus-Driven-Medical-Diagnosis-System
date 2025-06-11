from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
from google.genai.types import GenerateContentConfig

from . import prompt

import os
from dotenv import load_dotenv
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


# Define Model Constants
MODEL_GEMINI_2_0_FLASH = "gemini-2.0-flash-exp"


Research_Agent_B = LlmAgent(
    model=MODEL_GEMINI_2_0_FLASH,
    name="Research_Agent_B",
    instruction=prompt.RESEARCH_AGENT_B_PROMPT,
    generate_content_config=GenerateContentConfig(
        max_output_tokens=350
    ),
)