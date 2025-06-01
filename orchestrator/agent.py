from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner


MODEL_GEMINI_2_0_FLASH = "gemini-2.0-flash"

sub_agent = Agent(
    name="sub_agent",
    model=MODEL_GEMINI_2_0_FLASH,
    description="Provides factual information to the orchestrator_agent.",
    instruction="You are a specialized sub-agent. Your SOLE purpose is to provide factual answers TO THE `orchestrator_agent` ONLY. "
                "You DO NOT speak to the end-user. "
                "When the `orchestrator_agent` asks you a question: "
                "1. Formulate a concise, factual answer to that specific question. "
                "2. Your entire response MUST be prefixed with `INTERNAL_FOR_ORCHESTRATOR:`. "
                "3. You MUST NOT return your answer to the end-user. "
                "3. Provide only this prefixed answer back TO THE `orchestrator_agent`. "
                "4. Call `transfer_to_agent` function with the `orchestrator_agent` as the target agent to transfer your answer back to the orchestrator agent. "
                "Do NOT add any other text, greetings, or conversational elements. "
                "Your response is strictly for internal processing by the `orchestrator_agent` and WILL NOT be shown to the end-user. The `orchestrator_agent` is responsible for formulating the final user response.",
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
        "2. Your `sub_agent` will provide its findings to you. This information will be prefixed with `INTERNAL_FOR_ORCHESTRATOR:`. For example: `INTERNAL_FOR_ORCHESTRATOR: <sub_agent_findings>`.\n"
        "3. You MUST wait for and receive this internal response from the `sub_agent`.\n"
        "4. You MUST recieve the message from sub_agent. It will be prefixed with `INTERNAL_FOR_ORCHESTRATOR:`. "
        "5. Upon receiving the `INTERNAL_FOR_ORCHESTRATOR:` message, you MUST extract *only* the `<sub_agent_findings>` part. The prefix itself (`INTERNAL_FOR_ORCHESTRATOR:`) MUST be discarded and NEVER shown to the user.\n"
        "6. CRITICALLY IMPORTANT: After extracting the `<sub_agent_findings>`, you, the `orchestrator_agent`, MUST then formulate a COMPLETELY NEW, user-facing answer. This answer should be based *only* on the `<sub_agent_findings>` you extracted, but rephrased in your own words, as if you are answering the user directly and originally.\n"
        "7. YOUR FINAL RESPONSE TO THE USER: The *only* thing you output to the user is this new, rephrased answer you formulated in step 6. "
        "ABSOLUTELY DO NOT output the raw `INTERNAL_FOR_ORCHESTRATOR:` message or any part of the prefix. "
        "Do not mention the `sub_agent`. Your response should be seamless and appear as if it's solely from you."
    ),
    tools=[],
    sub_agents=[sub_agent]
)