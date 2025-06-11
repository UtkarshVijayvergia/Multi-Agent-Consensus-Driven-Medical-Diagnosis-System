import asyncio
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part, GenerateContentConfig
from google.adk.events import Event
from google.adk.tools.agent_tool import AgentTool

from .sub_agents.research_agent_A import Research_Agent_A
from .sub_agents.research_agent_B import Research_Agent_B
from .sub_agents.critiv_agent_A import Critic_Agent_A

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
    tools=[
        AgentTool(agent=Research_Agent_A),
        AgentTool(agent=Research_Agent_B),
        AgentTool(agent=Critic_Agent_A),
    ],
)

root_agent = Conductor_Agent

APP_NAME = "orchestrator"
USER_ID = "user_1"
SESSION_ID = "session_001"