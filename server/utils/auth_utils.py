import firebase_admin
from firebase_admin import auth, credentials
from flask import request, jsonify
from functools import wraps

# Initialize Firebase Admin SDK (use your service account key)
if not firebase_admin._apps:
    cred = credentials.Certificate("utils/serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

# Decorator to verify Firebase token and whitelist user
def verify_firebase_token_and_whitelist(f):
    @wraps(f)
    async def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization", None)
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401

        id_token = auth_header.split("Bearer ")[1]
        try:
            decoded_token = auth.verify_id_token(id_token)
            request.user = decoded_token  # Optionally attach user info to request
        except Exception as e:
            return jsonify({"error": "Invalid or expired token"}), 401

        return await f(*args, **kwargs)
    return decorated_function
