import os
import time
import logging
from datetime import datetime, timezone
from flask import Flask, request, jsonify

from auth import verify_token, authenticate_user, create_token
from rate_limiter import rate_limiter_user, rate_limiter_admin
from cost_guard import cost_guard
from utils.mock_llm import ask

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

START_TIME = time.time()

@app.route("/")
def root():
    return jsonify({
        "app": "AI Agent (Flask Mode)",
        "status": "running",
        "python_version": "3.14 compatible"
    })

@app.route("/auth/token", methods=["POST"])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400
    
    username = data.get("username")
    password = data.get("password")
    
    user = authenticate_user(username, password)
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401
        
    token = create_token(user["username"], user["role"])
    return jsonify({
        "access_token": token,
        "token_type": "bearer"
    })

@app.route("/ask", methods=["POST"])
def ask_agent():
    user, error = verify_token()
    if error:
        return jsonify({"error": error}), 401
        
    data = request.get_json()
    if not data or "question" not in data:
        return jsonify({"error": "question required"}), 400
        
    username = user["username"]
    role = user["role"]
    question = data["question"]

    # Rate Limit
    limiter = rate_limiter_admin if role == "admin" else rate_limiter_user
    allowed, info = limiter.check(username)
    if not allowed:
        return jsonify({"error": "Rate limit exceeded", "retry_after": info}), 429

    # Cost Guard
    allowed, error = cost_guard.check_budget(username)
    if not allowed:
        return jsonify({"error": error}), 402

    # Call LLM
    response_text = ask(question)

    # Record usage
    input_tokens = len(question.split()) * 2
    output_tokens = len(response_text.split()) * 2
    usage = cost_guard.record_usage(username, input_tokens, output_tokens)

    return jsonify({
        "question": question,
        "answer": response_text,
        "usage": {
            "remaining_requests": info if isinstance(info, int) else 0,
            "cost_usd": usage.total_cost_usd
        }
    })

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "uptime": round(time.time() - START_TIME, 1)
    })

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"\n=== Flask Mode (Python 3.14 Compatible) ===")
    print(f"Server running on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port)