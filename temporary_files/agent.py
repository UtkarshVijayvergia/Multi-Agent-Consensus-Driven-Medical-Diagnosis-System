from google.adk.agents import LoopAgent, LlmAgent, BaseAgent, SequentialAgent
from google.genai import types
from google.adk.runners import InMemoryRunner
from google.adk.agents.invocation_context import InvocationContext
from google.adk.tools.tool_context import ToolContext
from typing import AsyncGenerator, Optional
from google.adk.events import Event, EventActions
from google.genai.types import GenerateContentConfig
from google.adk.tools.agent_tool import AgentTool
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_response import LlmResponse
from datetime import datetime

from . import prompt

import os
from dotenv import load_dotenv
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


# Define Model Constants
MODEL_GEMINI_2_0_FLASH = "gemini-2.0-flash-exp"
APP_NAME = "medical_consultation"
USER_ID = "dev_user_01"
SESSION_ID_BASE = "dev_session_01"
DEV_PATIENT_QUERY = "I have a headache and feel dizzy. What could be the cause?"



# Define Callback Functions
# Define Callback Context
def increment_round_if_no_consensus(callback_context: CallbackContext, llm_response: LlmResponse) -> Optional[LlmResponse]:
    """
    Increments the round number in the session state if the consensus is NOT reached.
    Should be used as `after_model_callback` in Evaluate_Consensus_Agent.
    """
    # Defensive check: response must exist
    if not llm_response.content or not llm_response.content.parts:
        return None

    # Check the agent's response text
    response_text = llm_response.content.parts[0].text.lower()

    if "consensus reached" not in response_text:
        current_round = callback_context.state.get("round", 1)
        callback_context.state["round"] = current_round + 1

    # Return None to indicate that we are not modifying the LLM's output
    return None



class ConversationMemoryManager:
    def __init__(self, history_key: str = "conversation_history"):
        self.history_key = history_key

    def update_history(self, callback_context: CallbackContext, llm_response: LlmResponse) -> Optional[LlmResponse]:
        """Append the agent's response to shared conversation history in state."""
        if not llm_response.content or not llm_response.content.parts:
            return None  # nothing to append

        agent_name = callback_context.agent_name or "UnknownAgent"
        round_number = callback_context.state.get("round", 1)
        timestamp = datetime.utcnow().isoformat()

        text = llm_response.content.parts[0].text or "[No Text]"
        new_entry = (
            f"\n--- Round {round_number} | {agent_name} | {timestamp} ---\n{text}\n"
        )

        previous = callback_context.state.get(self.history_key, "")
        callback_context.state[self.history_key] = previous + new_entry

        return None  # return None to use the original LLM response

memory_manager = ConversationMemoryManager() # Create memory manager instance



# Define Tools
def exit_loop(tool_context: ToolContext):
    """Call this function ONLY when the critique indicates no further changes are needed, signaling the iterative process should end."""
    print(f"  [Tool Call] exit_loop triggered by {tool_context.agent_name}")
    tool_context.actions.escalate = True
    # Return empty dict as tools should typically return JSON-serializable output
    return {}



# Define LLM Agents
Research_Agent_A = LlmAgent(
    model=MODEL_GEMINI_2_0_FLASH,
    name="Research_Agent_A",
    instruction=prompt.RESEARCH_AGENT_A_PROMPT,
    generate_content_config=GenerateContentConfig(
        max_output_tokens=350
    ),
    output_key="Research_Agent_A_output",
    after_model_callback=memory_manager.update_history,
)


Research_Agent_B = LlmAgent(
    model=MODEL_GEMINI_2_0_FLASH,
    name="Research_Agent_B",
    instruction=prompt.RESEARCH_AGENT_B_PROMPT,
    generate_content_config=GenerateContentConfig(
        max_output_tokens=350
    ),
    output_key="Research_Agent_B_output",
    after_model_callback=memory_manager.update_history,
)


Critic_Agent_A = LlmAgent(
    model=MODEL_GEMINI_2_0_FLASH,
    name="Critic_Agent_A",
    instruction=prompt.CRITICAL_AGENT_A_PROMPT,
    generate_content_config=GenerateContentConfig(
        max_output_tokens=350
    ),
    output_key="Critic_Agent_A_output",
    after_model_callback=memory_manager.update_history,
)


Evaluate_Consensus_Agent = LlmAgent(
    model=MODEL_GEMINI_2_0_FLASH,
    name="Evaluate_Consensus_Agent",
    instruction=prompt.EVALUATE_CONSENSUS_AGENT_PROMPT,
    generate_content_config=GenerateContentConfig(
        max_output_tokens=100
    ),
    tools=[exit_loop],
    after_model_callback=increment_round_if_no_consensus,
)


Summarizer_Agent = LlmAgent(
    model=MODEL_GEMINI_2_0_FLASH,
    name="Summarizer_Agent",
    instruction=prompt.SUMMARIZER_AGENT_PROMPT,
    generate_content_config=GenerateContentConfig(
        max_output_tokens=350
    ),
)



# Define Workflow Agent
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



# Define Root Agent
root_agent = SequentialAgent(
    name="Medical_Consultation_Pipeline",
    sub_agents=[
        Loop_Agent,
        Summarizer_Agent,
    ],
    description="Root agent for the medical consultation pipeline, orchestrating the workflow of diagnosis and treatment planning.",
)