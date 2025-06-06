import asyncio
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

# Load environment variables from .env file
import os
from dotenv import load_dotenv
load_dotenv()

# get env variables
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Define constants
APP_NAME = "workflow_2_app"
USER_ID = "user1"
SESSION_ID = "workflow2_session"
MODEL = "gemini-2.0-flash"
NUM_ROUNDS = 3

# Define agents with output_key that will be overwritten later
agentA = LlmAgent(
    name="AgentA",
    model=MODEL,
    instruction="You are AgentA. Provide your opinion and comment on others if their views are provided.",
)

agentB = LlmAgent(
    name="AgentB",
    model=MODEL,
    instruction="You are AgentB. Provide your opinion and comment on others if their views are provided.",
)

agentC = LlmAgent(
    name="AgentC",
    model=MODEL,
    instruction="You are AgentC. Provide your opinion and comment on others if their views are provided.",
)

conductor = LlmAgent(
    name="ConductorAgent",
    model=MODEL,
    instruction="You are a conductor coordinating a multi-agent discussion.",
)

# --- Run multi-round discussion ---
async def run_workflow_2():
    session_service = InMemorySessionService()
    await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)

    user_question = "What are the potential benefits and risks of AI in healthcare?"

    for round_num in range(1, NUM_ROUNDS + 1):
        print(f"\n🔁 Round {round_num} Starting...\n")

        # Step 1: Each agent responds to user question + prior conductor summary
        for agent in [agentA, agentB, agentC]:
            agent.output_key = f"{agent.name}_thoughts_round{round_num}"
            runner = Runner(agent=agent, app_name=APP_NAME, session_service=session_service)

            prompt = f"Round {round_num} — Original Question: {user_question}"
            if round_num > 1:
                prompt += f"\n\nConductor Summary from Last Round:\n{{conductor_summary_round{round_num - 1}}}"

            async for event in runner.run_async(
                user_id=USER_ID,
                session_id=SESSION_ID,
                new_message=Content(parts=[Part(text=prompt)], role="user")
            ):
                if event.is_final_response() and event.content:
                    print(f"[{agent.name}] {event.content.parts[0].text.strip()}")


        # Step 2: Conductor summarizes responses
        conductor_output_key = f"conductor_summary_round{round_num}"
        conductor.output_key = conductor_output_key

        views = "\n".join([
            f"{agent.name}: {{ {agent.name}_thoughts_round{round_num} }}"
            for agent in [agentA, agentB, agentC]
        ])
        conductor.instruction = f"""You are a conductor.
You received the following responses in round {round_num}:\n\n{views}

Please summarize their perspectives and give them something to reflect on and respond to in the next round.
"""

        runner = Runner(agent=conductor, app_name=APP_NAME, session_service=session_service)
        async for event in runner.run_async(
            user_id=USER_ID,
            session_id=SESSION_ID,
            new_message=Content(parts=[Part(text=prompt)], role="user")
        ):
            if event.is_final_response() and event.content:
                print(f"[{agent.name}] {event.content.parts[0].text.strip()}")

    # Show final state
    session = await session_service.get_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
    print("\n✅ Final session.state:\n")
    for key, val in session.state.items():
        print(f"{key}:\n{val[:300]}{'...' if len(val) > 300 else ''}\n")

# --- Entry Point ---
if __name__ == "__main__":
    asyncio.run(run_workflow_2())
