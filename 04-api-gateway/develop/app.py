"""
BASIC — API Key Authentication (Flask version for Python 3.14)

Lớp bảo vệ đơn giản nhất: kiểm tra header X-API-Key.

Chạy:
    $env:AGENT_API_KEY="my-secret-123"
    python app.py

Test (PowerShell):
    # Có key → 200
    Invoke-RestMethod -Uri "http://localhost:8000/ask?question=Hello" -Method Post -Headers @{"X-API-Key"="my-secret-123"}

    # Không có key → 401
    Invoke-RestMethod -Uri "http://localhost:8000/ask?question=Hello" -Method Post
"""
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

# ──────────────────────────────────────
# Mock LLM
# ──────────────────────────────────────
def ask(question: str):
    return f"Tôi là AI agent được deploy lên cloud. Câu hỏi của bạn: {question}"

# ──────────────────────────────────────
# API Key setup
# ──────────────────────────────────────
API_KEY = os.getenv("AGENT_API_KEY", "demo-key-change-in-production")


def verify_api_key():
    """Kiểm tra API key từ header X-API-Key."""
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return None, "Missing API key. Include header: X-API-Key: <your-key>"
    if api_key != API_KEY:
        return None, "Invalid API key."
    return api_key, None


# ──────────────────────────────────────
# Endpoints
# ──────────────────────────────────────

@app.route("/")
def root():
    """Public endpoint — không cần auth"""
    return jsonify({"message": "AI Agent API", "auth": "Required for /ask"})


@app.route("/ask", methods=["POST"])
def ask_agent():
    """Protected endpoint — cần X-API-Key header"""
    key, error = verify_api_key()
    if error:
        status = 401 if "Missing" in error else 403
        return jsonify({"detail": error}), status

    question = request.args.get("question", "hello")
    return jsonify({
        "question": question,
        "answer": ask(question),
    })


@app.route("/health")
def health():
    """Health check — public (platform cần access)"""
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"API Key: {API_KEY}")
    print(f"Server: http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
