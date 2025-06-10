import asyncio
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part, GenerateContentConfig
from google.adk.events import Event

from . import prompt

import os
from dotenv import load_dotenv
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


# Define Model Constants
MODEL_GEMINI_2_0_FLASH = "gemini-2.0-flash-exp"


Conductor_Agent = LlmAgent(
    model=MODEL_GEMINI_2_0_FLASH,
    name="Conductor_Agent",
    instruction=prompt.CONDUCTOR_PROMPT,
    generate_content_config=GenerateContentConfig(
        max_output_tokens=100
    ),
)