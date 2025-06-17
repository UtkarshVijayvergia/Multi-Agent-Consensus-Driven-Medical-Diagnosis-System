from google.adk.events import Event, EventActions
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types

from .orchestrator_agent.agent import root_agent

import os
from dotenv import load_dotenv
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
AGENT_MODEL = os.getenv("AGENT_MODEL")



# Define constants for identifying the interaction context
APP_NAME = "medical_consultation"
USER_ID = "dev_user_01"
SESSION_ID = "dev_session_01"
DEV_PATIENT_QUERY = "I am a 23 year old male. I am feeling cold and have slight cough for the past 2 days. I don't have fever. I also have no history of any chronic diseases or respiratory disease."

# Create the specific session where the conversation will happen
session_service = InMemorySessionService()

# Runner orchestrates the agent execution loop.
runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service
)

# Interact with the Agent
# async def call_agent_async(query: str, runner, user_id, session_id):
#     """Sends a query to the agent and prints the final response."""
#     print(f"\n>>> User Query: {query}")

#     # Prepare the user's message in ADK format
#     content = types.Content(role='user', parts=[types.Part(text=query)])
#     final_response_text = "Agent did not produce a final response."

#     agent_conversation_history = {}

#     async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
#         if event.content and event.content.parts:
#             agent_name = event.author or "UnknownAgent"
#             # Always start from 1, use round from metadata if present, else use last round + 1
#             if hasattr(event, "metadata") and event.metadata and "round" in event.metadata:
#                 round_number = event.metadata["round"]
#             else:
#                 # Fallback: find max round so far and increment
#                 prev_rounds = [
#                     int(k.split("_round_")[1].split("_")[0])
#                     for k in agent_conversation_history.keys()
#                     if "_round_" in k and k.startswith(agent_name)
#                 ]
#                 round_number = max(prev_rounds, default=0) + 1

#             if agent_name == "Summarizer_Agent":
#                 key = agent_name
#             else:
#                 key = f"{agent_name}_round_{round_number}"

#             # If key already exists, enumerate to avoid overwriting
#             base_key = key
#             i = 2
#             while key in agent_conversation_history:
#                 key = f"{base_key}_{i}"
#                 i += 1

#             # Aggregate all text parts
#             texts = []
#             for part in event.content.parts:
#                 if hasattr(part, "text") and part.text:
#                     texts.append(part.text)
#             if texts:
#                 agent_conversation_history[key] = "\n".join(texts)
    
#     print("Agent Conversation History:")
#     for k, v in agent_conversation_history.items():
#         print(f"{k}: {v}")


async def call_agent_and_return_history(query: str, runner, user_id, session_id):
    """Sends a query to the agent and returns the conversation history as a dict."""
    content = types.Content(role='user', parts=[types.Part(text=query)])
    agent_conversation_history = {}

    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        if event.content and event.content.parts:
            agent_name = event.author or "UnknownAgent"
            if hasattr(event, "metadata") and event.metadata and "round" in event.metadata:
                round_number = event.metadata["round"]
            else:
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

            base_key = key
            i = 2
            while key in agent_conversation_history:
                key = f"{base_key}_{i}"
                i += 1

            texts = []
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    texts.append(part.text)
            if texts:
                agent_conversation_history[key] = "\n".join(texts)
    return agent_conversation_history


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