import time
from collections import defaultdict

from redis.asyncio import Redis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app); self.redis = Redis.from_url(settings.redis_url, decode_responses=True); self.memory = defaultdict(int)

    async def dispatch(self, request: Request, call_next):
        if request.url.path.endswith(("/health/live", "/health/ready", "/metrics")):
            return await call_next(request)
        client = request.client.host if request.client else "unknown"; bucket = int(time.time() // 60); key = f"rate:{client}:{bucket}"
        try:
            count = await self.redis.incr(key)
            if count == 1: await self.redis.expire(key, 70)
        except Exception:
            self.memory[key] += 1; count = self.memory[key]
        if count > settings.rate_limit_per_minute:
            return JSONResponse({"detail":"Rate limit exceeded"}, status_code=429, headers={"Retry-After":"60"})
        response = await call_next(request); response.headers["X-RateLimit-Limit"] = str(settings.rate_limit_per_minute); response.headers["X-RateLimit-Remaining"] = str(max(0, settings.rate_limit_per_minute-count)); return response
