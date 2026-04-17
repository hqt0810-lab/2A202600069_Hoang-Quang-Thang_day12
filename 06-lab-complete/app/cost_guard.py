import time
import logging
from fastapi import HTTPException
from app.config import settings

logger = logging.getLogger(__name__)

# Đơn giá mock (USD/1000 tokens)
PRICE_INPUT = 0.00015
PRICE_OUTPUT = 0.0006

class CostGuard:
    def __init__(self):
        self._daily_cost = 0.0
        self._reset_day = time.strftime("%Y-%m-%d")
        self._redis = None
        
        if settings.redis_url:
            try:
                import redis
                self._redis = redis.from_url(settings.redis_url, decode_responses=True)
                self._redis.ping()
                logger.info("Connected to Redis for Cost Guard")
            except Exception:
                self._redis = None

    def _get_current_cost(self):
        today = time.strftime("%Y-%m-%d")
        if self._redis:
            val = self._redis.get(f"cost:{today}")
            return float(val) if val else 0.0
        
        # In-memory reset
        if today != self._reset_day:
            self._daily_cost = 0.0
            self._reset_day = today
        return self._daily_cost

    def check_budget(self):
        """Kiểm tra xem đã vượt ngân sách ngày chưa."""
        current = self._get_current_cost()
        if current >= settings.daily_budget_usd:
            logger.warning(f"Budget exhausted: {current} >= {settings.daily_budget_usd}")
            raise HTTPException(
                status_code=503, 
                detail="Daily budget exhausted. Please try again tomorrow."
            )
        return current

    def record_usage(self, input_tokens: int, output_tokens: int):
        """Tính toán và ghi nhận chi phí."""
        cost = (input_tokens / 1000) * PRICE_INPUT + (output_tokens / 1000) * PRICE_OUTPUT
        today = time.strftime("%Y-%m-%d")
        
        if self._redis:
            new_cost = self._redis.incrbyfloat(f"cost:{today}", cost)
            self._redis.expire(f"cost:{today}", 86400 * 2) # Giữ 2 ngày
            return new_cost
        
        self._daily_cost += cost
        return self._daily_cost

# Singleton
cost_guard = CostGuard()
