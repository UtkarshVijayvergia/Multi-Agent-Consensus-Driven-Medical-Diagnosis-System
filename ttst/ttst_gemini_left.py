import asyncio
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part, GenerateContentConfig
from google.adk.events import Event

# Load environment variables from .env file
import os
from dotenv import load_dotenv
load_dotenv()

# get env variables
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


APP_NAME = "workflow_2_full_history"
USER_ID = "user1"
SESSION_ID = "full_history_consensus"
# Using a model that is effective at following instructions and generating structured output.
MODEL = "gemini-1.5-flash"


agentA = LlmAgent(
    name="AgentA",
    model=MODEL,
    instruction=(
        "You are AgentA, the lead diagnostician in a doctor's consultation team. "
        "You have two colleagues, AgentB and AgentC."
        "The patient's symptoms are provided in the conversation history. "
        "Your task is to analyze the patient's query and provide an initial, detailed diagnosis and treatment plan. "
        "Clearly state your reasoning. Your colleagues will then review and discuss your proposal."
    ),    
    generate_content_config=GenerateContentConfig(
        max_output_tokens=350
    )
)

agentB = LlmAgent(
    name="AgentB",
    model=MODEL,
    instruction=(
        "You are AgentB, a part of a doctor's consultation team with AgentA and AgentC. "
        "The patient's symptoms and the conversation history, including AgentA's initial diagnosis, are provided. "
        "Your task is to carefully review the proposed diagnosis and treatment plan. "
        "You may agree with the plan, disagree, ask clarifying questions, point out potential mistakes, or suggest alternative approaches to help build a consensus."
    ),
    generate_content_config=GenerateContentConfig(
        max_output_tokens=350
    )
)

agentC = LlmAgent(
    name="AgentC",
    model=MODEL,
    instruction=(
        "You are AgentC, a part of a doctor's consultation team with AgentA and AgentB. "
        "The patient's symptoms and the conversation history, including all previous agent responses, are provided. "
        "Your task is to carefully review the ongoing discussion and the proposed diagnosis and treatment plan. "
        "You may agree, disagree, ask clarifying questions, identify errors, or suggest alternatives to help the team reach a final, robust consensus."
    ),
    generate_content_config=GenerateContentConfig(
        max_output_tokens=350
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
    instruction=(
        "You are a conductor overseeing a medical consultation between three agents. "
        "Based on the latest round of discussion, determine if a clear consensus on a diagnosis and treatment plan has been reached. "
        "If a consensus is reached, respond with 'Consensus Reached:' followed by a comprehensive summary of the final diagnosis and treatment plan suitable for the patient. "
        "If there are still disagreements or open questions, respond with 'Discussion continues.' and nothing more."
    ),
    generate_content_config=GenerateContentConfig(
        max_output_tokens=500
    )
)

# --- Main Workflow ---
async def run_workflow_with_full_history():
    session_service = InMemorySessionService()
    
    # Initial user question is the first event in the session
    # user_question = "I’m a 42-year-old woman and have started experiencing pain and stiffness in my hands and knees, especially in the mornings. The pain eases up after some movement, but it returns later in the day. I haven’t had any injuries or falls, and I’m not overweight. I’m also feeling more tired than usual. What could be causing these symptoms, and what should I do next?"
    user_question = "I am a 23 year old male and I have a slight cough from last 2 days. Should I take Azithromycin or Amoxicillin for it?"
    round_num = 1
    consensus_reached = False
    AGENTS = ["AgentA", "AgentB", "AgentC"]
    
    session = await session_service.create_session(
        app_name=APP_NAME, 
        user_id=USER_ID, 
        session_id=SESSION_ID,
        # events=[initial_event] # Start the session with the user's question
    )
    
    initial_event = Event(
        author="user", 
        content=Content(parts=[Part(text=user_question)])
    )
    
    await session_service.append_event(session, initial_event)

    runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)

    while not consensus_reached:
        print(f"\n🔁 Round {round_num} Started")
        
        # Agents respond. The framework will provide the full history automatically.
        for name in AGENTS:
            runner.agent = agent_map[name]
            runner.agent.output_key = f"{name}_thoughts_round{round_num}"
            
            # It only needs to instruct the agent on the task for THIS turn.
            # prompt = (
            #     f"The user's medical question is in the conversation history. "
            #     f"This is Round {round_num}. "
            #     f"{name}, Your task is to reflect on the entire conversation history provided, including previous rounds, and continue the conversation by providing your response. "
            #     f"You may agree, disagree, ask questions to other agents, find mistakes in other agents' responses and answer questions asked by other agents agents."
            # )
            prompt = (
                f"You are {name}, a part of the doctors' consultation team consisting of 3 doctors - AgentA, AgentB, and AgentC. "
                f"You are an expert medical diagnostician. "
                f"Your colleagues will also be providing their medical opinions. "
                f"This is Round {round_num}. "
                f"The patient's symptoms and the past conversation history your colleagues are provided in the conversation history. "
                f"Your primary task is to analyze all the information and discuss with your colleagues to design a potential diagnosis and treatment plan based on the patient's symptoms. "
                f"You may agree or disagree with your colleagues, ask questions to your colleagues, find mistakes in other colleagues' responses and answer questions asked colleagues."
            )
            
            async for event in runner.run_async(
                user_id=USER_ID,
                session_id=SESSION_ID,
                # The new message is just the prompt for the current turn.
                new_message=Content(parts=[Part(text=prompt)], role="user")
            ):
                if event.is_final_response() and event.content:
                    print(f"[{name}]\n{event.content.parts[0].text.strip()}\n")
        
        # Conductor logic remains the same, as it correctly reads from state.
        session = await session_service.get_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
        conductor_prompt = "Here are the latest responses from this round:\n\n"
        for name in AGENTS:
            key = f"{name}_thoughts_round{round_num}"
            val = session.state.get(key, "[No response recorded]")
            conductor_prompt += f"{name}: {val}\n"
        
        runner.agent = root_agent
        runner.agent.output_key = f"conductor_check_round{round_num}"

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
