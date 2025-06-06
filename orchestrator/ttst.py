# Import necessary libraries
import os
import asyncio
from google.adk.agents import Agent
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm # For multi-model support
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types # For creating message Content/Parts
from google.adk.tools.agent_tool import AgentTool
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse, LlmRequest
from typing import Optional

import warnings
# Ignore all warnings
warnings.filterwarnings("ignore")

import logging
logging.basicConfig(level=logging.ERROR)

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# get env variables
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Define Model Constants
MODEL_GEMINI_2_0_FLASH = "gemini-2.0-flash-exp"




# --- Define your before callback function ---
# def my_before_model_logic(callback_context: CallbackContext, llm_request: LlmRequest) -> Optional[LlmResponse]:
#     print(f"\n\nbefore Callback: {callback_context.agent_name}")
#     # if llm_request.config.system_instruction if context.state['lang'] == 'Hindi'
#     if llm_request.contents:
#         print(f"before: function_call: {llm_request.contents[-1].parts[0].function_call}")
#         print(f"before: Text__content: {llm_request.contents[-1].parts[0].text}")
#         print(f"before: function_resp: {llm_request.contents[-1].parts[0].function_response} \n") 
#     else:
#         print(f"before: No content in response.")
#     return None # Allow the model call to proceed


# # --- Define your after model callback function ---
# def my_after_model_logic(callback_context: CallbackContext, llm_response: LlmResponse) -> Optional[LlmResponse]:
#     print(f"after Callback: {callback_context.agent_name}")
#     if llm_response.content:
#         print(f"after: function_call: {llm_response.content.parts[0].function_call}")
#         print(f"after: Text__content: {llm_response.content.parts[0].text}")
#         print(f"after: function_resp: {llm_response.content.parts[0].function_response}")
#     else:
#         print(f"after: ---- No content in response.")
#     return llm_response # Return the response to continue the flow





root_agent = LlmAgent(
    name="Genius",
    model=MODEL_GEMINI_2_0_FLASH, # Can be a string for Gemini or a LiteLlm object
    description="The main coordinator agent that communicates with the user.",
    instruction="Provide helpful and accurate responses to user queries.",
    tools=[],
    # before_model_callback=my_before_model_logic,
    # after_model_callback=my_after_model_logic
)

APP_NAME = "test_app"
USER_ID = "user_1"
SESSION_ID = "session_001"

session_service = InMemorySessionService()



async def create_session():
    """Create a session for the app."""
    return await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
        state={"test:" : "test_value", "spam": "eggs", "preferred_distance_unit": "centimeter"}
    )

# Create a session for the app
import asyncio
session = asyncio.run(create_session())
# Ensure the session is created successfully
if session is None:
    raise ValueError("Session creation failed. Please check the session service configuration.")


print(f"Created session object: {session}") 

runner = Runner(
    agent=root_agent, # The agent we want to run
    app_name=APP_NAME,   # Associates runs with our app
    session_service=session_service # Uses our session manager
)
# print(f"Runner created for agent '{runner.agent.name}'.")
# print(f"Content of session_service.sessions: {session_service.sessions}") # Modified to clarify what is being printed






async def call_agent_async(query: str, runner, user_id, session_id):
    """Sends a query to the agent and prints the final response."""
    print(f"\n>>> User Query: {query}")

    # Prepare the user's message in ADK format
    content = types.Content(role='user', parts=[types.Part(text=query)])

    final_response_text = "Agent did not produce a final response." # Default

    # Key Concept: run_async executes the agent logic and yields Events.
    # We iterate through events to find the final answer.
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        # You can uncomment the line below to see *all* events during execution
        print(f"  [Event] Author: {event.author}, Type: {type(event).__name__}, Final: {event.is_final_response()}, Content: {event.content}")

        # Check for message from sub_agent to orchestrator_agent
        if event.author == "sub_agent" and event.content and event.content.parts:
            part = event.content.parts[0]
            if part.function_call and part.function_call.name == "transfer_to_agent":
                if part.function_call.args and part.function_call.args.get('agent_name') == "orchestrator_agent":
                    # The sub_agent's instruction is to send "TransferMessage = \"sub_agent: \" + your_factual_answer"
                    # This message is typically passed as an argument to transfer_to_agent.
                    # Let's assume the argument key for the message content is 'message' or 'TransferMessage'.
                    # We'll check for common names or print all args if not found.
                    message_content = None
                    if 'message' in part.function_call.args:
                        message_content = part.function_call.args['message']
                    elif 'TransferMessage' in part.function_call.args: # As per sub_agent's prompt
                        message_content = part.function_call.args['TransferMessage']
                    elif 'content' in part.function_call.args: # Another common possibility
                        message_content = part.function_call.args['content']
                    
                    if message_content:
                        print(f"  [INFO] sub_agent to orchestrator_agent: {message_content}")
                    else:
                        # If the specific key isn't found, print all args to help identify it.
                        print(f"  [INFO] sub_agent to orchestrator_agent (raw args): {part.function_call.args}")

        # Key Concept: is_final_response() marks the concluding message for the turn.
        if event.is_final_response():
            if event.content and event.content.parts:
                # Assuming text response in the first part
                final_response_text = event.content.parts[0].text
            elif event.actions and event.actions.escalate: # Handle potential errors/escalations
                final_response_text = f"Agent escalated: {event.error_message or 'No specific message.'}"
            # Add more checks here if needed (e.g., specific error codes)
            break # Stop processing events once the final response is found

    print(f"<<< Agent Response: {final_response_text}")





# @title Run the Initial Conversation

# We need an async function to await our interaction helper
async def run_conversation():
    await call_agent_async("What is the weather like in London?", runner=runner, user_id=USER_ID, session_id=SESSION_ID)


# # Uncomment the following lines if running as a standard Python script (.py file):
# import asyncio
# if __name__ == "__main__":
#     try:
#         asyncio.run(run_conversation())
#     except Exception as e:
#         print(f"An error occurred: {e}")