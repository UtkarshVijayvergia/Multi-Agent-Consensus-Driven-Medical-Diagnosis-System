import asyncio
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part, GenerateContentConfig
from google.adk.events import Event

# Load environment variables from .env file
import os
from dotenv import load_dotenv
load_dotenv()

# get env variables
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


