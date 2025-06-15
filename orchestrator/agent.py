from google.adk.agents import SequentialAgent

from .sub_agents.workflow_agents.agent import Loop_Agent
from .sub_agents.summarizer_agent import Summarizer_Agent

import os
from dotenv import load_dotenv
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


root_agent = SequentialAgent(
    name="Medical_Consultation_Pipeline",
    sub_agents=[
        Loop_Agent,
        Summarizer_Agent,
    ],
    description="Root agent for the medical consultation pipeline, orchestrating the workflow of diagnosis and treatment planning.",
)