import time
from collections import defaultdict
from fastapi import HTTPException, Request, status

class limiter:
    def __init__(self, limit: int = 5, window: int = 60, requests_limit: int | None = None, time_window_seconds: int | None = None):
        self.limit = requests_limit if requests_limit is not None else limit
        self.window = time_window_seconds if time_window_seconds is not None else window
        self.history: dict[str, list[float]] = defaultdict(list)

    async def __call__(self, req: Request) -> None:
        ip = req.client.host if req.client else "unknown"
        now = time.time()
        start = now - self.window
        reqs = [t for t in self.history[ip] if t > start]
        if len(reqs) >= self.limit:
            retry = int(self.window - (now - reqs[0])) + 1
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Слишком много попыток. Пожалуйста, повторите через {retry} сек.",
                headers={"Retry-After": str(max(retry, 1))})
        reqs.append(now)
        self.history[ip] = reqs

RateLimiter = limiter
