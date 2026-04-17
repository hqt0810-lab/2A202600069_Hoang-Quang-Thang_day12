import time
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

PRICE_PER_1K_INPUT_TOKENS = 0.00015
PRICE_PER_1K_OUTPUT_TOKENS = 0.0006

@dataclass
class UsageRecord:
    user_id: str
    input_tokens: int = 0
    output_tokens: int = 0
    request_count: int = 0
    day: str = field(default_factory=lambda: time.strftime("%Y-%m-%d"))

    @property
    def total_cost_usd(self) -> float:
        input_cost = (self.input_tokens / 1000) * PRICE_PER_1K_INPUT_TOKENS
        output_cost = (self.output_tokens / 1000) * PRICE_PER_1K_OUTPUT_TOKENS
        return round(input_cost + output_cost, 6)

class CostGuard:
    def __init__(self, daily_budget_usd=1.0, global_daily_budget_usd=10.0):
        self.daily_budget_usd = daily_budget_usd
        self.global_daily_budget_usd = global_daily_budget_usd
        self._records = {}
        self._global_cost = 0.0

    def _get_record(self, user_id):
        today = time.strftime("%Y-%m-%d")
        record = self._records.get(user_id)
        if not record or record.day != today:
            self._records[user_id] = UsageRecord(user_id=user_id, day=today)
        return self._records[user_id]

    def check_budget(self, user_id):
        record = self._get_record(user_id)
        if self._global_cost >= self.global_daily_budget_usd:
            return False, "Global budget exceeded"
        if record.total_cost_usd >= self.daily_budget_usd:
            return False, "User budget exceeded"
        return True, None

    def record_usage(self, user_id, input_tokens, output_tokens):
        record = self._get_record(user_id)
        record.input_tokens += input_tokens
        record.output_tokens += output_tokens
        record.request_count += 1
        cost = (input_tokens / 1000 * PRICE_PER_1K_INPUT_TOKENS +
                output_tokens / 1000 * PRICE_PER_1K_OUTPUT_TOKENS)
        self._global_cost += cost
        return record

    def get_usage(self, user_id):
        record = self._get_record(user_id)
        return {
            "user_id": user_id,
            "cost_usd": record.total_cost_usd,
            "budget_usd": self.daily_budget_usd,
        }

cost_guard = CostGuard()
