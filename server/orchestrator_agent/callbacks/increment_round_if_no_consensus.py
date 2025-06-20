# round_increment_callback.py

from typing import Optional
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_response import LlmResponse

def increment_round_if_no_consensus(callback_context: CallbackContext, llm_response: LlmResponse) -> Optional[LlmResponse]:
    """
    Increments the round number in the session state if the consensus is NOT reached.
    Should be used as `after_model_callback` in Evaluate_Consensus_Agent.
    """
    # Defensive check: response must exist
    if not llm_response.content or not llm_response.content.parts:
        return None

    # Get the first part of the response
    response_part = llm_response.content.parts[0]

    # Check if the response part contains text before accessing it
    if response_part.text:
        response_text = response_part.text.lower()
        if "consensus reached" not in response_text:
            current_round = callback_context.state.get("round", 1)
            callback_context.state["round"] = current_round + 1

    # Return None to indicate that we are not modifying the LLM's output
    return None