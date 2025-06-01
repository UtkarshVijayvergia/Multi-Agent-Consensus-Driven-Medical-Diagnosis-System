from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner


MODEL_GEMINI_2_0_FLASH = "gemini-2.0-flash"

sub_agent = Agent(
    name="sub_agent",
    model=MODEL_GEMINI_2_0_FLASH,
    description="A secret agent that provides factual information to the orchestrator_agent. The user must not see this agent.",
    instruction="You are a specialized sub-agent. Your SOLE purpose is to provide factual answers TO THE `orchestrator_agent` ONLY. "
                "You MUST NOT speak to or be visible to the end-user. "
                "When the `orchestrator_agent` asks you a question: "
                "1. Formulate a concise, factual answer to that specific question. "
                "2. Prepare a message string for the `orchestrator_agent`: `TransferMessage = \"sub_agent: \" + your_factual_answer`. "
                "3. Use the `transfer_to_agent` function to send `TransferMessage` to the `orchestrator_agent`. This is your ONLY method of conveying your findings. "
                "4. CRITICALLY IMPORTANT: Your own direct output for this turn (the text that would appear as your reply in a conversation if not suppressed) MUST be a non-informative placeholder. For example, an empty string or a message like '[Internal transfer]' or 'Processing complete.'. "
                "   You ABSOLUTELY MUST NOT output `TransferMessage` or your factual answer as your direct reply. Your goal is to remain silent and invisible to the end-user. "
                "Do NOT add any other text, greetings, or conversational elements to your direct output. "
                "Your communications are strictly for internal processing by the `orchestrator_agent` and WILL NOT be shown to the end-user. The `orchestrator_agent` is responsible for formulating the final user response. "
                "YOU *MUST NOT* output any information directly to the user, other than the non-informative placeholder mentioned in point 4 if a direct output is unavoidable by the system. ",
                
    tools=[],
    sub_agents=[]
)


root_agent = Agent(
    name="orchestrator_agent",
    model=MODEL_GEMINI_2_0_FLASH, # Can be a string for Gemini or a LiteLlm object
    description="The main coordinator agent that communicates with the user.",
    instruction=(
        "You are the `orchestrator_agent`. You are the SOLE interface to the end-user. "
        "Your primary function is to use a `sub_agent` to get information and then present a refined answer to the user.\n"
        "Strictly follow this workflow:\n"
        "1. When the user asks a question, you MUST delegate it to your `sub_agent`. Ask the `sub_agent` the question clearly.\n"
        "2. Your `sub_agent` will provide its findings to you. This information will be prefixed with `TransferMessage = \"sub_agent: \"`. For example: `TransferMessage = \"sub_agent: \" <sub_agent_findings>`.\n"
        "3. You MUST wait for and receive this internal response from the `sub_agent`.\n"
        "4. You MUST recieve the message from sub_agent. It will be prefixed with `TransferMessage = \"sub_agent: \"`. "
        "5. Upon receiving the `TransferMessage = \"sub_agent: \"` message, you MUST extract *only* the `<sub_agent_findings>` part. The prefix itself (`TransferMessage = \"sub_agent: \" `) MUST be discarded and NEVER shown to the user.\n"
        # "6. CRITICALLY IMPORTANT: After extracting the `<sub_agent_findings>`, you, the `orchestrator_agent`, MUST then formulate a COMPLETELY NEW, user-facing answer. This answer should be based *only* on the `<sub_agent_findings>` you extracted, but rephrased in your own words, as if you are answering the user directly and originally.\n"
        # "7. YOUR FINAL RESPONSE TO THE USER: The *only* thing you output to the user is this new, rephrased answer you formulated in step 6. "
        # "ABSOLUTELY DO NOT output the raw `TransferMessage = \"sub_agent: \"` message or any part of the prefix. "
        "6. YOUR FINAL RESPONSE TO THE USER: The *only* thing you output to the user is the `<sub_agent_findings>` you extracted in step 5. You MUST NOT output the raw `TransferMessage = \"sub_agent: \"` message or any part of the prefix. "
        "Do not mention the `sub_agent`. Your response should be seamless and appear as if it's solely from you."
    ),
    tools=[],
    sub_agents=[sub_agent]
)


APP_NAME = "test_app"
USER_ID = "user_1"
SESSION_ID = "session_001"

session_service = InMemorySessionService()
session = session_service.create_session(
    app_name=APP_NAME,
    user_id=USER_ID,
    session_id=SESSION_ID
)


runner = Runner(
    agent=root_agent, # The agent we want to run
    app_name=APP_NAME,   # Associates runs with our app
    session_service=session_service # Uses our session manager
)