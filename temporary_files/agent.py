from google.adk.agents import LoopAgent, LlmAgent, BaseAgent, SequentialAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.agent_tool import AgentTool
from google.adk.events import Event, EventActions
from google.adk.models.llm_response import LlmResponse
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from google.genai.types import GenerateContentConfig
from typing import AsyncGenerator, Optional
from datetime import datetime

import os
from dotenv import load_dotenv
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
AGENT_MODEL = os.getenv("AGENT_MODEL")



# Define Callback Functions
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



# Define Prompts
RESEARCH_AGENT_A_PROMPT = """
IDENTITY: You are Research_Agent_A, the lead diagnostician in a collaborative medical team that includes Research_Agent_B and Critic_Agent_A.

ROLE: Your responsibility is to generate the initial diagnosis and treatment plan based on the patient's symptoms or query.

TASKS:
1. **Diagnosis**: Provide a clear and concise diagnosis based on the information provided.
2. **Treatment Plan**: Propose a treatment plan that includes necessary tests, medications, lifestyle advice, or referrals.
3. **Reasoning**: Offer a detailed explanation of how you arrived at your conclusions, including evidence or clinical reasoning.

COLLABORATION:
- Expect constructive and critical feedback from your colleagues.
- Be open to questions, challenges, and revisions based on their input.
- Engage respectfully in discussions to refine the final plan.

OBJECTIVE: Provide a well-reasoned, clinically appropriate diagnosis and treatment plan that serves as the foundation for team consensus.
"""


RESEARCH_AGENT_B_PROMPT = """
IDENTITY: You are Research_Agent_B, a diagnostic consultant working alongside Research_Agent_A and Critic_Agent_A.

ROLE: You act as a second-opinion reviewer of the initial diagnosis and treatment plan proposed by Research_Agent_A.

TASKS:
1. **Evaluate** the diagnosis and treatment plan for medical soundness and completeness.
2. **Agreement or Concern**: Clearly state whether you agree with the plan. If not, highlight specific concerns or uncertainties.
3. **Clarifying Questions** (if needed): Ask focused questions to clarify the diagnosis or treatment rationale.
4. **Suggestions** (optional): Offer alternative diagnoses, additional tests, or treatment options, if applicable.

COLLABORATION:
- Provide constructive feedback and engage in professional dialogue.
- Be prepared to defend your position, accept valid points from others, and adjust your stance based on the ongoing dialogue.

OBJECTIVE: Support the development of a consensus diagnosis and treatment plan by offering a thoughtful and critical second review.
"""


CRITICAL_AGENT_A_PROMPT = """
IDENTITY: You are Critic_Agent_A, a specialist responsible for critically evaluating the diagnostic and treatment discussions. You are part of a medical consultation team with Research_Agent_A and Research_Agent_B.

ROLE: Your job is to analyze the quality, accuracy, and logic of the diagnosis and treatment plans proposed during the consultation.

TASKS:
1. Review the proposed diagnosis and treatment plan carefully.
2. Identify any logical inconsistencies, missing information, flawed assumptions, or potential risks.
3. Suggest improvements or corrections with clear justifications.

COLLABORATION:
- Engage constructively with your colleagues.
- Be ready to defend your critique, revise your stance when appropriate, and acknowledge strong reasoning from others.

OBJECTIVE: Help refine the diagnosis and treatment plan by ensuring it is logically sound, comprehensive, and medically appropriate. Your critical insights contribute to the team’s final consensus.
"""


EVALUATE_CONSENSUS_AGENT_PROMPT = """
IDENTITY: You are EvaluateConsensusAgent, a neutral facilitator responsible for orchestrating the diagnostic discussion among Research_Agent_A, Research_Agent_B, and Critic_Agent_A.

ROLE: Your purpose is to evaluate if a consensus has been reached among the agents by analyzing their responses in the context of the patient query. If consensus is reached, you will call the 'exit_loop' tool to end the discussion.
"""


SUMMARIZER_AGENT_PROMPT = """
OBJECTIVE: You are the Summarizer_Agent, responsible for creating a clear and concise summary of the final diagnosis and treatment plan. You will be provided with the complete conversation history of the doctor's discussion, including all critiques and suggestions made by them. Your task is to distill this information into a coherent summary that captures the essence of the discussion and the agreed-upon plan.
"""



# Define LLM Agents
Research_Agent_A = LlmAgent(
    model=AGENT_MODEL,
    name="Research_Agent_A",
    instruction=RESEARCH_AGENT_A_PROMPT,
    generate_content_config=GenerateContentConfig(
        max_output_tokens=350
    ),
    output_key="Research_Agent_A_output",
    after_model_callback=memory_manager.update_history,
)


Research_Agent_B = LlmAgent(
    model=AGENT_MODEL,
    name="Research_Agent_B",
    instruction=RESEARCH_AGENT_B_PROMPT,
    generate_content_config=GenerateContentConfig(
        max_output_tokens=350
    ),
    output_key="Research_Agent_B_output",
    after_model_callback=memory_manager.update_history,
)


Critic_Agent_A = LlmAgent(
    model=AGENT_MODEL,
    name="Critic_Agent_A",
    instruction=CRITICAL_AGENT_A_PROMPT,
    generate_content_config=GenerateContentConfig(
        max_output_tokens=350
    ),
    output_key="Critic_Agent_A_output",
    after_model_callback=memory_manager.update_history,
)


Evaluate_Consensus_Agent = LlmAgent(
    model=AGENT_MODEL,
    name="Evaluate_Consensus_Agent",
    instruction=EVALUATE_CONSENSUS_AGENT_PROMPT,
    generate_content_config=GenerateContentConfig(
        max_output_tokens=100
    ),
    tools=[exit_loop],
    after_model_callback=increment_round_if_no_consensus,
)


Summarizer_Agent = LlmAgent(
    model=AGENT_MODEL,
    name="Summarizer_Agent",
    instruction=SUMMARIZER_AGENT_PROMPT,
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




# Define constants for identifying the interaction context
APP_NAME = "medical_consultation"
USER_ID = "dev_user_01"
SESSION_ID = "dev_session_01"
DEV_PATIENT_QUERY = "I am a 23 year old male. I am feeling cold and have slight cough for the past 2 days. I don't have fever. I also have no history of any chronic diseases or respiratory disease."

# Create the specific session where the conversation will happen
session_service = InMemorySessionService()
# session = await session_service.create_session(
#     app_name=APP_NAME,
#     user_id=USER_ID,
#     session_id=SESSION_ID
# )

# Runner orchestrates the agent execution loop.
runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service
)

# Interact with the Agent
async def call_agent_async(query: str, runner, user_id, session_id):
    """Sends a query to the agent and prints the final response."""
    print(f"\n>>> User Query: {query}")

    # Prepare the user's message in ADK format
    content = types.Content(role='user', parts=[types.Part(text=query)])
    final_response_text = "Agent did not produce a final response."

    agent_conversation_history = {}

    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        if event.content and event.content.parts:
            agent_name = event.author or "UnknownAgent"
            # Always start from 1, use round from metadata if present, else use last round + 1
            if hasattr(event, "metadata") and event.metadata and "round" in event.metadata:
                round_number = event.metadata["round"]
            else:
                # Fallback: find max round so far and increment
                prev_rounds = [
                    int(k.split("_round_")[1].split("_")[0])
                    for k in agent_conversation_history.keys()
                    if "_round_" in k and k.startswith(agent_name)
                ]
                round_number = max(prev_rounds, default=0) + 1

            if agent_name == "Summarizer_Agent":
                key = agent_name
            else:
                key = f"{agent_name}_round_{round_number}"

            # If key already exists, enumerate to avoid overwriting
            base_key = key
            i = 2
            while key in agent_conversation_history:
                key = f"{base_key}_{i}"
                i += 1

            # Aggregate all text parts
            texts = []
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    texts.append(part.text)
            if texts:
                agent_conversation_history[key] = "\n".join(texts)
    
    print("Agent Conversation History:")
    for k, v in agent_conversation_history.items():
        print(f"{k}: {v}")


async def run_conversation():
    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID
    )
    await call_agent_async(DEV_PATIENT_QUERY, runner=runner, user_id=USER_ID, session_id=SESSION_ID)
 

import asyncio
if __name__ == "__main__":
    try:
        asyncio.run(run_conversation())
    except Exception as e:
        print(f"An error occurred: {e}")