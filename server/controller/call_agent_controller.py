from google.adk.events import Event, EventActions
from google.genai import types

import os
from dotenv import load_dotenv
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
AGENT_MODEL = os.getenv("AGENT_MODEL")



# Define constants for identifying the interaction context
APP_NAME = "medical_consultation"
USER_ID = "dev_user_01"
SESSION_ID = "dev_session_01"




async def call_agent_and_return_history(query: str, runner, user_id, session_id):
    """
    Sends a query to the agent and returns the conversation history
    as an ordered list of dictionaries (FIFO).
    """
    content = types.Content(role='user', parts=[types.Part(text=query)])
    
    # The final result is a list to guarantee order for the frontend.
    agent_conversation_history = []
    
    # We use a set to track keys we've already used to replicate the original
    # file's logic for handling key collisions.
    keys_seen = set()

    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        if event.content and event.content.parts:
            # --- This logic carefully replicates the original key generation ---
            agent_name = event.author or "UnknownAgent"
            
            if hasattr(event, "metadata") and event.metadata and "round" in event.metadata:
                round_number = event.metadata["round"]
            else:
                prev_rounds = [
                    int(k.split("_round_")[1].split("_")[0])
                    for k in keys_seen
                    if "_round_" in k and k.startswith(agent_name)
                ]
                round_number = max(prev_rounds, default=0) + 1

            if agent_name == "Summarizer_Agent":
                key = agent_name
            else:
                key = f"{agent_name}_round_{round_number}"

            base_key = key
            i = 2
            # This loop handles key collisions exactly as before.
            while key in keys_seen:
                key = f"{base_key}_{i}"
                i += 1
            keys_seen.add(key)
            # --- End of key generation logic ---
            
            texts = []
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    texts.append(part.text)
            
            if texts:
                # Append a dictionary for the current turn to the list.
                # This preserves the First-In, First-Out order of events.
                agent_conversation_history.append({
                    "agent": key,
                    "response": "\n".join(texts)
                })

    return agent_conversation_history