from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from flask import Flask, request, jsonify
from flask_cors import CORS  # Import the CORS library
import asyncio

from orchestrator_agent.agent import root_agent
from utils.auth_utils import verify_firebase_token_and_whitelist
from controller.call_agent_controller import call_agent_and_return_history


# --- Constants ---
USER_ID = "dev_user_01"
SESSION_ID = "dev_session_01"
APP_NAME = "medical_consultation"


# --- Flask App Initialization ---
app = Flask(__name__)


# --- FIX: Enable CORS ---
# This will allow requests from any origin.
# For production, you might want to restrict this to your frontend's domain.
CORS(app)


# --- Routes ---
@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@app.route("/submit_query", methods=["POST"])
@verify_firebase_token_and_whitelist
async def submit_query():
    data = request.get_json()
    if not data or "query" not in data:
        return jsonify({"error": "Missing 'query' in request"}), 400

    user_query = data["query"]

    # Create the specific session where the conversation will happen
    session_service = InMemorySessionService()
    # Runner orchestrates the agent execution loop.
    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service
    )

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



# This block allows you to run the app as a module
if __name__ == "__main__":
    print("--- Starting Flask Application as a module ---")
    app.run(host='0.0.0.0', port=5000, debug=False)