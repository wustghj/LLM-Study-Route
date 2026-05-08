"""
gateway.py — Phase 5D：最小 LLM API 网关

用途：一个能上线的 LLM 服务中间层。解决三个最基本的生产问题：
  1. 鉴权：验证调用方身份
  2. 限流：防止被刷爆
  3. 日志：每次请求都留痕

架构：
  客户端 → Gateway (FastAPI, :8000) → 上游 LLM (DeepSeek / Ollama)
              │
              ├─ API Key 验证中间件
              ├─ Token Bucket 限流
              ├─ JSON Lines 请求日志
              └─ SSE 流式透传

启动：
  pip install fastapi uvicorn aiohttp
  $env:DEEPSEEK_API_KEY = "sk-..."
  python gateway.py

然后：
  curl -X POST http://localhost:8000/v1/chat/completions \
    -H "Authorization: Bearer test-key-001" \
    -H "Content-Type: application/json" \
    -d '{"model":"deepseek-chat","messages":[{"role":"user","content":"你好"}],"stream":true}'

设计理念：
  这不是生产级网关（生产请用 Kong / Nginx + auth plugin）。
  这是一个学习工具——让你理解网关的每一层在做什么。
"""

import asyncio
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from fastapi import FastAPI, Request, HTTPException
    from fastapi.responses import StreamingResponse, JSONResponse
    import uvicorn
except ImportError:
    print("需要 fastapi 和 uvicorn：pip install fastapi uvicorn aiohttp", file=sys.stderr)
    raise

try:
    import aiohttp
except ImportError:
    print("需要 aiohttp：pip install aiohttp", file=sys.stderr)
    raise


# =========================================================================
# 配置
# =========================================================================

UPSTREAM_URL = os.getenv("UPSTREAM_URL", "https://api.deepseek.com/v1")
UPSTREAM_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
GATEWAY_PORT = int(os.getenv("GATEWAY_PORT", "8000"))
LOG_PATH = Path(os.getenv("GATEWAY_LOG_PATH", "logs/gateway_requests.jsonl"))

# 简单的 API Key "数据库"（生产请用真正的数据库或密钥管理服务）
API_KEYS: dict[str, dict[str, Any]] = {
    "test-key-001": {"name": "测试用户 1", "rate_limit": 30},   # 每分钟 30 次
    "test-key-002": {"name": "测试用户 2", "rate_limit": 60},   # 每分钟 60 次
    "admin-key":    {"name": "管理员",     "rate_limit": 300},  # 每分钟 300 次
}


# =========================================================================
# Token Bucket 限流器
# =========================================================================

class TokenBucket:
    """
    经典令牌桶算法。

    每个 API Key 有一个桶，容量 = rate_limit。
    每秒补充 rate_limit/60 个令牌。
    每次请求消耗 1 个令牌。令牌不足 → 429 Too Many Requests。
    """

    def __init__(self, rate_limit: int):
        self.rate_limit = rate_limit
        self.tokens = float(rate_limit)  # 初始满桶
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def consume(self) -> bool:
        """尝试消耗 1 个令牌。成功返回 True，否则 False。"""
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            # 补充令牌（速率 = rate_limit / 60 每秒）
            refill = elapsed * (self.rate_limit / 60.0)
            self.tokens = min(float(self.rate_limit), self.tokens + refill)
            self.last_refill = now

            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False


class RateLimiter:
    """管理所有 API Key 的令牌桶。"""

    def __init__(self):
        self._buckets: dict[str, TokenBucket] = {}

    def get_bucket(self, api_key: str) -> TokenBucket:
        if api_key not in self._buckets:
            key_info = API_KEYS.get(api_key, {"rate_limit": 10})
            self._buckets[api_key] = TokenBucket(key_info["rate_limit"])
        return self._buckets[api_key]


# =========================================================================
# 结构化日志（复用 Phase 5A 的模式）
# =========================================================================

class GatewayLogger:
    def __init__(self, log_path: Path = LOG_PATH):
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, **kwargs: Any) -> dict:
        kwargs.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        kwargs.setdefault("request_id", uuid.uuid4().hex[:12])
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(kwargs, ensure_ascii=False) + "\n")
        return kwargs


# =========================================================================
# FastAPI 应用
# =========================================================================

app = FastAPI(
    title="LLM Gateway",
    description="最小 LLM API 网关 — 鉴权 / 限流 / 日志 / 流式透传",
    version="0.1.0",
)
rate_limiter = RateLimiter()
gateway_logger = GatewayLogger()


# --- 中间件：API Key 鉴权 + 限流 ---

@app.middleware("http")
async def auth_and_rate_limit(request: Request, call_next):
    """每个请求进来先过鉴权和限流。"""

    # 健康检查不需要鉴权
    if request.url.path == "/health":
        return await call_next(request)

    # 1. 鉴权：检查 Authorization header
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"error": "未提供 API Key。请加 Header: Authorization: Bearer <key>"},
        )

    api_key = auth_header.removeprefix("Bearer ").strip()
    if api_key not in API_KEYS:
        return JSONResponse(
            status_code=401,
            content={"error": "API Key 无效"},
        )

    # 2. 限流：检查令牌桶
    bucket = rate_limiter.get_bucket(api_key)
    if not await bucket.consume():
        return JSONResponse(
            status_code=429,
            content={
                "error": "请求太频繁，被限流了",
                "retry_after_seconds": 5,
            },
            headers={"Retry-After": "5"},
        )

    # 把 API Key 信息存到 request.state，后续 handler 可以用
    request.state.api_key = api_key
    request.state.api_key_name = API_KEYS[api_key]["name"]

    return await call_next(request)


# --- 健康检查 ---

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "upstream": UPSTREAM_URL,
        "uptime": "since last restart",
    }


# --- 核心：Chat Completions 代理 ---

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """
    代理 /v1/chat/completions，支持流式和非流式。

    请求体格式和 OpenAI API 完全一致：
      {"model": "...", "messages": [...], "stream": true/false, ...}
    """
    body = await request.json()
    model = body.get("model", "unknown")
    stream = body.get("stream", False)
    messages = body.get("messages", [])

    # 构造上游请求
    upstream_payload = {
        "model": model,
        "messages": messages,
        "stream": stream,
        "temperature": body.get("temperature", 0.7),
        "max_tokens": body.get("max_tokens", 2048),
    }
    upstream_headers = {
        "Authorization": f"Bearer {UPSTREAM_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream" if stream else "application/json",
    }

    upstream_url = f"{UPSTREAM_URL.rstrip('/')}/chat/completions"
    request_id = uuid.uuid4().hex[:12]

    # 非流式：直接转发
    if not stream:
        t0 = time.perf_counter()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    upstream_url,
                    json=upstream_payload,
                    headers=upstream_headers,
                    timeout=aiohttp.ClientTimeout(total=120),
                ) as response:
                    upstream_body = await response.json()
                    elapsed = int((time.perf_counter() - t0) * 1000)

                    usage = upstream_body.get("usage", {})
                    gateway_logger.log(
                        request_id=request_id,
                        api_key=request.state.api_key,
                        api_key_name=request.state.api_key_name,
                        model=model,
                        stream=False,
                        input_tokens=usage.get("prompt_tokens", 0),
                        output_tokens=usage.get("completion_tokens", 0),
                        total_ms=elapsed,
                        status="success" if response.status == 200 else "error",
                        upstream_status=response.status,
                    )
                    return JSONResponse(content=upstream_body, status_code=response.status)

        except Exception as exc:
            elapsed = int((time.perf_counter() - t0) * 1000)
            gateway_logger.log(
                request_id=request_id,
                api_key=request.state.api_key,
                model=model,
                stream=False,
                total_ms=elapsed,
                status="error",
                error=str(exc)[:200],
            )
            return JSONResponse(status_code=502, content={"error": f"上游连接失败: {exc}"})

    # 流式：边收边转发（SSE 透传）
    t0 = time.perf_counter()
    first_token_at = None
    output_tokens = 0

    async def stream_proxy():
        nonlocal first_token_at, output_tokens
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    upstream_url,
                    json=upstream_payload,
                    headers=upstream_headers,
                    timeout=aiohttp.ClientTimeout(total=120),
                ) as response:
                    if response.status != 200:
                        body = await response.text()
                        yield f"data: {json.dumps({'error': f'上游返回 {response.status}: {body[:200]}'})}\n\n"
                        yield "data: [DONE]\n\n"
                        return

                    async for line in response.content:
                        text = line.decode("utf-8", errors="replace")
                        yield text  # 原样透传

                        if first_token_at is None and '"content":"' in text:
                            first_token_at = time.perf_counter()
                        output_tokens += 1  # 粗略计数

        except Exception as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"
            yield "data: [DONE]\n\n"
        finally:
            elapsed = int((time.perf_counter() - t0) * 1000)
            ft = int((first_token_at - t0) * 1000) if first_token_at else None
            gateway_logger.log(
                request_id=request_id,
                api_key=request.state.api_key,
                api_key_name=request.state.api_key_name,
                model=model,
                stream=True,
                first_token_ms=ft,
                output_tokens=output_tokens,
                total_ms=elapsed,
                status="success",
            )

    return StreamingResponse(
        stream_proxy(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Request-ID": request_id,
        },
    )


# --- 网关状态 ---

@app.get("/stats")
async def stats():
    """查看网关基本状态（API Key 使用情况）。"""
    key_stats = {}
    for key, info in API_KEYS.items():
        bucket = rate_limiter.get_bucket(key)
        key_stats[key] = {
            "name": info["name"],
            "rate_limit": info["rate_limit"],
            "available_tokens": round(bucket.tokens, 1),
        }

    return {
        "upstream": UPSTREAM_URL,
        "model": os.getenv("UPSTREAM_MODEL", "default"),
        "api_keys": key_stats,
    }


# =========================================================================
# 启动
# =========================================================================

def print_startup():
    print(f"""
╔══════════════════════════════════════════════════════╗
║              LLM Gateway 已启动                       ║
╠══════════════════════════════════════════════════════╣
║  地址：    http://localhost:{GATEWAY_PORT}                      ║
║  上游：    {UPSTREAM_URL[:45]:<45s}  ║
║  健康检查：http://localhost:{GATEWAY_PORT}/health               ║
║  状态：    http://localhost:{GATEWAY_PORT}/stats                ║
║  API 文档：http://localhost:{GATEWAY_PORT}/docs                 ║
╠══════════════════════════════════════════════════════╣
║  测试：                                              ║
║  curl -X POST http://localhost:{GATEWAY_PORT}/v1/chat/completions \\ ║
║    -H "Authorization: Bearer test-key-001" \\        ║
║    -H "Content-Type: application/json" \\            ║
║    -d '{{"model":"deepseek-chat","messages":[{{"role":"user","content":"你好"}}],"stream":false}}' ║
╚══════════════════════════════════════════════════════╝
""")


if __name__ == "__main__":
    if not UPSTREAM_API_KEY:
        print("错误：请设置上游 API Key", file=sys.stderr)
        print("  $env:DEEPSEEK_API_KEY = 'sk-...'", file=sys.stderr)
        print("  $env:UPSTREAM_URL = 'http://localhost:11434/v1'  # 或指向 Ollama", file=sys.stderr)
        sys.exit(1)

    print_startup()
    uvicorn.run(app, host="0.0.0.0", port=GATEWAY_PORT, log_level="info")
