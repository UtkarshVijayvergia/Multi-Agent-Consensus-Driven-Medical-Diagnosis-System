from google.adk.agents import Agent

# from dotenv import load_dotenv
# load_dotenv()
# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
# GOOGLE_GENAI_USE_VERTEXAI = os.getenv("GOOGLE_GENAI_USE_VERTEXAI")


MODEL_GEMINI_2_0_FLASH = "gemini-2.0-flash"

root_agent = Agent(
    name="orchestrator_agent",
    model=MODEL_GEMINI_2_0_FLASH, # Can be a string for Gemini or a LiteLlm object
    description="Provides answers to user's questions.",
    instruction="You are an orchestrator agent that answers question by using Gemini LLM",
    tools=[],
)

