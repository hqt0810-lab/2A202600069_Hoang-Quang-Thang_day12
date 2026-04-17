"""
Production AI Agent — Final Version
"""
import os
import time
import logging
import json
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Internal modules
from app.config import settings
from app.auth import verify_api_key
from app.rate_limiter import check_rate_limit
from app.cost_guard import cost_guard

# Utils
from utils.mock_llm import ask as llm_ask

# ─────────────────────────────────────────────────────────
# Logging — JSON structured
# ─────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format='{"ts":"%(asctime)s","lvl":"%(levelname)s","msg":"%(message)s"}',
)
logger = logging.getLogger(__name__)

START_TIME = time.time()
_is_ready = False
_request_count = 0
_error_count = 0

# ─────────────────────────────────────────────────────────
# Lifespan
# ─────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    global _is_ready
    logger.info(json.dumps({
        "event": "startup",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }))
    _is_ready = True
    yield
    _is_ready = False
    logger.info(json.dumps({"event": "shutdown"}))

# ─────────────────────────────────────────────────────────
# App Setup
# ─────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)

@app.middleware("http")
async def request_middleware(request: Request, call_next):
    global _request_count, _error_count
    start = time.time()
    _request_count += 1
    try:
        response: Response = await call_next(request)
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        if "server" in response.headers:
            del response.headers["server"]
        duration = round((time.time() - start) * 1000, 1)
        
        # Log request if not health check
        if request.url.path not in ["/health", "/ready"]:
            logger.info(json.dumps({
                "event": "request",
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "ms": duration,
            }))
        return response
    except Exception as e:
        _error_count += 1
        logger.error(json.dumps({"event": "error", "msg": str(e)}))
        raise

# ─────────────────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────────────────
class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)

class AskResponse(BaseModel):
    question: str
    answer: str
    model: str
    usage: dict
    timestamp: str

# ─────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────

@app.get("/", tags=["Info"])
def root():
    return {
        "app": settings.app_name,
        "status": "running",
        "environment": settings.environment,
        "docs": "/docs" if settings.environment != "production" else "disabled"
    }

@app.post("/ask", response_model=AskResponse, tags=["Agent"])
async def ask_agent(
    body: AskRequest,
    _key: str = Depends(verify_api_key),
):
    """AI Agent endpoint with Security, Rate Limiting and Cost Guard."""
    
    # 1. Rate Limit Check (sử dụng 8 ký tự đầu của API Key làm identifier)
    rate_info = check_rate_limit(_key[:8])

    # 2. Budget Check
    current_cost = cost_guard.check_budget()

    # 3. LLM Call
    answer = llm_ask(body.question)

    # 4. Usage Recording
    input_tokens = len(body.question.split()) * 2
    output_tokens = len(answer.split()) * 2
    total_cost = cost_guard.record_usage(input_tokens, output_tokens)

    return AskResponse(
        question=body.question,
        answer=answer,
        model=settings.llm_model,
        usage={
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "current_daily_cost_usd": round(total_cost, 5),
            "rate_limit_remaining": rate_info.get("remaining"),
            "storage_source": rate_info.get("source")
        },
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

@app.get("/health", tags=["Ops"])
def health():
    return {
        "status": "ok",
        "uptime": round(time.time() - START_TIME, 1),
        "requests": _request_count,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/ready", tags=["Ops"])
def ready():
    if not _is_ready:
        return Response(status_code=503)
    return {"status": "ready"}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
