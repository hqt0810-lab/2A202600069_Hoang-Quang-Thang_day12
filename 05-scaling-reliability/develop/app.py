"""
BASIC — Health Check + Graceful Shutdown (Flask version for Python 3.14)

Hai tính năng tối thiểu cần có trước khi deploy:
  1. GET /health  — liveness: "agent có còn sống không?"
  2. GET /ready   — readiness: "agent có sẵn sàng nhận request chưa?"
  3. Graceful shutdown: hoàn thành request hiện tại trước khi tắt

Chạy:
    python app.py

Test:
    Invoke-RestMethod -Uri http://localhost:8000/health
    Invoke-RestMethod -Uri http://localhost:8000/ready
"""
import os
import time
import signal
import logging
import threading
from datetime import datetime, timezone
from flask import Flask, jsonify, request

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

START_TIME = time.time()
_is_ready = False
_in_flight_requests = 0
_lock = threading.Lock()

# Mock LLM
def ask(question: str):
    return f"Tôi là AI agent được deploy lên cloud. Câu hỏi của bạn: {question}"


# ──────────────────────────────────────────────────────────
# Middleware — track in-flight requests
# ──────────────────────────────────────────────────────────
@app.before_request
def before_request():
    global _in_flight_requests
    with _lock:
        _in_flight_requests += 1

@app.after_request
def after_request(response):
    global _in_flight_requests
    with _lock:
        _in_flight_requests -= 1
    return response


# ──────────────────────────────────────────────────────────
# Business Logic
# ──────────────────────────────────────────────────────────
@app.route("/")
def root():
    return jsonify({"message": "AI Agent with health checks!"})


@app.route("/ask", methods=["POST"])
def ask_agent():
    if not _is_ready:
        return jsonify({"error": "Agent not ready"}), 503

    data = request.get_json()
    question = data.get("question", "hello") if data else "hello"
    return jsonify({"answer": ask(question)})


# ──────────────────────────────────────────────────────────
# HEALTH CHECKS
# ──────────────────────────────────────────────────────────
@app.route("/health")
def health():
    """
    LIVENESS PROBE — "Agent có còn sống không?"
    """
    uptime = round(time.time() - START_TIME, 1)
    checks = {}

    try:
        import psutil
        mem = psutil.virtual_memory()
        checks["memory"] = {
            "status": "ok" if mem.percent < 90 else "degraded",
            "used_percent": mem.percent,
        }
    except ImportError:
        checks["memory"] = {"status": "ok", "note": "psutil not installed"}

    overall_status = "ok" if all(
        v.get("status") == "ok" for v in checks.values()
    ) else "degraded"

    return jsonify({
        "status": overall_status,
        "uptime_seconds": uptime,
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
    })


@app.route("/ready")
def ready():
    """
    READINESS PROBE — "Agent có sẵn sàng nhận request chưa?"
    """
    if not _is_ready:
        return jsonify({
            "ready": False,
            "detail": "Agent not ready. Check back in a few seconds.",
        }), 503

    return jsonify({
        "ready": True,
        "in_flight_requests": _in_flight_requests,
    })


# ──────────────────────────────────────────────────────────
# GRACEFUL SHUTDOWN
# ──────────────────────────────────────────────────────────
def handle_signal(signum, frame):
    global _is_ready
    logger.info(f"Received signal {signum} — initiating graceful shutdown")
    _is_ready = False

    timeout = 10
    elapsed = 0
    while _in_flight_requests > 0 and elapsed < timeout:
        logger.info(f"Waiting for {_in_flight_requests} in-flight requests...")
        time.sleep(1)
        elapsed += 1

    logger.info("Shutdown complete")
    raise SystemExit(0)

signal.signal(signal.SIGINT, handle_signal)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))

    # Simulate startup
    logger.info("Agent starting up...")
    logger.info("Loading model and checking dependencies...")
    time.sleep(0.2)
    _is_ready = True
    logger.info("Agent is ready!")

    app.run(host="0.0.0.0", port=port, debug=False)
