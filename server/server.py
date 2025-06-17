# server/server.py

from flask import Flask, request, jsonify
import asyncio

# This relative import is correct when run as a module.
from .call_agent import (
    call_agent_and_return_history,
    runner,
    session_service,
    APP_NAME
)

# --- Constants ---
USER_ID = "dev_user_01"
SESSION_ID = "dev_session_01"

# --- Flask App Initialization ---
app = Flask(__name__)

# --- Routes ---
@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route("/submit_query", methods=["POST"])
async def submit_query():
    """
    Receives the user query, runs the agent, and returns the agent's conversation history.
    Expects JSON: { "query": "..." }
    """
    data = request.get_json()
    if not data or "query" not in data:
        return jsonify({"error": "Missing 'query' in request"}), 400

    user_query = data["query"]

    try:
        await session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=SESSION_ID
        )
    except Exception as e:
        print(f"Session creation notice: {e}")

    agent_history = await call_agent_and_return_history(
        user_query, runner, USER_ID, SESSION_ID
    )

    return jsonify({"agent_conversation_history": agent_history})

# This block is crucial. When you run 'python -m server.server',
# this script's __name__ becomes '__main__', and this code executes.
if __name__ == "__main__":
    print("--- Starting Flask Application as a module ---")
    app.run(host='0.0.0.0', port=5000, debug=False)