import time
from collections import defaultdict, deque

class RateLimiter:
    def __init__(self, max_requests=10, window_seconds=60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._windows = defaultdict(deque)

    def check(self, user_id):
        now = time.time()
        window = self._windows[user_id]
        while window and window[0] < now - self.window_seconds:
            window.popleft()

        if len(window) >= self.max_requests:
            oldest = window[0]
            retry_after = int(oldest + self.window_seconds - now) + 1
            return False, retry_after

        window.append(now)
        return True, self.max_requests - len(window)

rate_limiter_user = RateLimiter(max_requests=10, window_seconds=60)
rate_limiter_admin = RateLimiter(max_requests=100, window_seconds=60)
