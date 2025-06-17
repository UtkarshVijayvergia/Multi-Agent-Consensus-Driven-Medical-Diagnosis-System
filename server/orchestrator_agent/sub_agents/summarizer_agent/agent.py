from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
from google.genai.types import GenerateContentConfig

from .prompt import SUMMARIZER_AGENT_PROMPT_V1
from ...tools.exit_loop import exit_loop

import os
from dotenv import load_dotenv
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
AGENT_MODEL = os.getenv("AGENT_MODEL")


Summarizer_Agent = LlmAgent(
    model=AGENT_MODEL,
    name="Summarizer_Agent",
    instruction=SUMMARIZER_AGENT_PROMPT_V1,
    generate_content_config=GenerateContentConfig(
        max_output_tokens=350
    ),
)