from datetime import datetime
from typing import Optional
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse

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
