from google.adk.agents import SequentialAgent, LoopAgent

from ..research_agent_A import Research_Agent_A
from ..research_agent_B import Research_Agent_B
from ..critic_agent_A import Critic_Agent_A
from ..evaluate_consensus_agent import Evaluate_Consensus_Agent

import os
from dotenv import load_dotenv
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


Sequential_Agent = SequentialAgent(
    name="Sequential_Agent",
    sub_agents=[
        Research_Agent_A,
        Research_Agent_B,
        Critic_Agent_A,
    ],
    description="Sequentially runs Research_Agent_A, Research_Agent_B, and Critic_Agent_A to generate a diagnosis and treatment plan.",
)


Loop_Agent = LoopAgent(
    name="Loop_Agent",
    sub_agents=[
        Sequential_Agent,
        Evaluate_Consensus_Agent,
    ],
    max_iterations=5,
)