import asyncio
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part, GenerateContentConfig

# Load environment variables from .env file
import os
from dotenv import load_dotenv
load_dotenv()


# workflow:
# - conductor_agent (the main agent) passes the question to agentA, agentB, and agentC.
# - agentA, agentB and agentC generates their comments/answers/research/etc and gives it back to conductor_agent
# - conductor_agent compiles the comments of all the 3 agents and passes back to each agent.
# - Now all the 3 agents will reply to other agent's views. They can either agree with them or contradict them and explain why. They can also ask a question to a particular agent 
# - This will keep happening untill a consensus is reached.

# get env variables
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

APP_NAME = "workflow_2_full_history"
USER_ID = "user1"
SESSION_ID = "full_history_consensus"
MODEL = "gemini-2.0-flash-exp"

# --- Predefined Agents ---
agentA = LlmAgent(
    name="AgentA",
    model=MODEL,
    instruction="""You are AgentA. You are part of a multi-agent discussion. In each round, you will receive the user question and the complete history of past responses. Reflect on all rounds before responding.""",
    generate_content_config=GenerateContentConfig(
        max_output_tokens=250
    )
)

agentB = LlmAgent(
    name="AgentB",
    model=MODEL,
    instruction="""You are AgentB. You are part of a multi-agent discussion. In each round, you will receive the user question and the complete history of past responses. Reflect on all rounds before responding.""",
    generate_content_config=GenerateContentConfig(
        max_output_tokens=250
    )
)

agentC = LlmAgent(
    name="AgentC",
    model=MODEL,
    instruction="""You are AgentC. You are part of a multi-agent discussion. In each round, you will receive the user question and the complete history of past responses. Reflect on all rounds before responding.""",
    generate_content_config=GenerateContentConfig(
        max_output_tokens=250
    )
)

agent_map = {
    "AgentA": agentA,
    "AgentB": agentB,
    "AgentC": agentC
}

root_agent = LlmAgent(
    name="ConductorAgent",
    model=MODEL,
    instruction="""You are a conductor. Given the latest round of agent responses, determine if all 3 agents are now in agreement.
If yes, say: 'Consensus reached.'
If not, say: 'Discussion continues.'"""
)

# --- Main Workflow ---
async def run_workflow_with_full_history():
    session_service = InMemorySessionService()
    await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)

    user_question = "I’m a 42-year-old woman and have started experiencing pain and stiffness in my hands and knees, especially in the mornings. The pain eases up after some movement, but it returns later in the day. I haven’t had any injuries or falls, and I’m not overweight. I’m also feeling more tired than usual. What could be causing these symptoms, and what should I do next?"
    round_num = 1
    consensus_reached = False
    AGENTS = ["AgentA", "AgentB", "AgentC"]

    while not consensus_reached:
        print(f"\n🔁 Round {round_num} Started")
        session = await session_service.get_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)

        # Build full history prompt from previous rounds using raw session state
        history_text = f"User Question: {user_question}\n\n"
        for past_round in range(1, round_num):
            history_text += f"--- Round {past_round} ---\n"
            for name in AGENTS:
                key = f"{name}_thoughts_round{past_round}"
                val = session.state.get(key, "[No response recorded]")
                history_text += f"{name}: {val}\n"
            history_text += "\n"

        # Agents respond to full history
        for name in AGENTS:
            agent = agent_map[name]
            agent.output_key = f"{name}_thoughts_round{round_num}"
            prompt = (
                f"{history_text}"
                f"--- Round {round_num} ---\n"
                f"{name}, please respond. Reflect on all agents' prior statements. "
                f"You may agree, disagree, or ask questions to AgentA, AgentB, or AgentC. "
                f"Do not summarize. Engage directly with the content."
            )

            runner = Runner(agent=agent, app_name=APP_NAME, session_service=session_service)

            async for event in runner.run_async(
                user_id=USER_ID,
                session_id=SESSION_ID,
                new_message=Content(parts=[Part(text=prompt)], role="user")
            ):
                if event.is_final_response() and event.content:
                    print(f"[{name}]\n{event.content.parts[0].text.strip()}\n")

        # Conductor checks for agreement
        session = await session_service.get_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
        conductor_prompt = "Here are the latest responses:\n\n"
        for name in AGENTS:
            key = f"{name}_thoughts_round{round_num}"
            val = session.state.get(key, "[No response recorded]")
            conductor_prompt += f"{name}: {val}\n"

        root_agent.output_key = f"conductor_check_round{round_num}"
        runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)

        verdict = ""
        async for event in runner.run_async(
            user_id=USER_ID,
            session_id=SESSION_ID,
            new_message=Content(parts=[Part(text=conductor_prompt)], role="user")
        ):
            if event.is_final_response() and event.content:
                verdict = event.content.parts[0].text.strip()
                print(f"[ConductorAgent]\n{verdict}\n")

        if "consensus reached" in verdict.lower():
            consensus_reached = True
        else:
            round_num += 1

    # Optional: Get final summary
    summary_prompt = (
        "Now that consensus is reached, please summarize the final key points "
        "from the discussion above in a clear and concise manner."
    )

    runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=Content(parts=[Part(text=summary_prompt)], role="user")
    ):
        if event.is_final_response() and event.content:
            print(f"📝 Final Summary:\n{event.content.parts[0].text.strip()}")

    # Print session state
    session = await session_service.get_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
    print("\n✅ Final session.state:\n")
    for key, val in session.state.items():
        print(f"FINAL: {key}:\n{val[:300]}{'...' if len(val) > 300 else ''}\n")


# --- Entry Point ---
if __name__ == "__main__":
    asyncio.run(run_workflow_with_full_history())
