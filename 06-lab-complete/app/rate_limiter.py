import time
import logging
from collections import defaultdict, deque
from fastapi import HTTPException
from app.config import settings

logger = logging.getLogger(__name__)

# Fallback in-memory storage
_rate_windows: dict[str, deque] = defaultdict(deque)

# Redis storage (optional)
_redis = None
if settings.redis_url:
    try:
        import redis
        _redis = redis.from_url(settings.redis_url, decode_responses=True)
        _redis.ping()
        logger.info("Connected to Redis for Rate Limiting")
    except Exception as e:
        logger.warning(f"Could not connect to Redis: {e}. Falling back to in-memory.")
        _redis = None

def check_rate_limit(key: str):
    """
    Kiểm tra rate limit sử dụng Sliding Window.
    Hỗ trợ Redis nếu được cấu hình, nếu không sẽ dùng bộ nhớ trong (không scale được).
    """
    limit = settings.rate_limit_per_minute
    now = time.time()

    if _redis:
        try:
            # Redis-based sliding window using ZSET
            pipe = _redis.pipeline()
            redis_key = f"rate_limit:{key}"
            pipe.zremrangebyscore(redis_key, 0, now - 60)
            pipe.zcard(redis_key)
            pipe.zadd(redis_key, {str(now): now})
            pipe.expire(redis_key, 65)
            _, count, _, _ = pipe.execute()

            if count >= limit:
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded: {limit} req/min (Redis)",
                    headers={"Retry-After": "60"},
                )
            return {"remaining": limit - count - 1, "source": "redis"}
        except Exception as e:
            logger.error(f"Redis rate limit error: {e}")
            # Fallback to memory if Redis fails

    # In-memory fallback
    window = _rate_windows[key]
    while window and window[0] < now - 60:
        window.popleft()
    
    if len(window) >= limit:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {limit} req/min (In-memory)",
            headers={"Retry-After": "60"},
        )
    
    window.append(now)
    return {"remaining": limit - len(window), "source": "memory"}
