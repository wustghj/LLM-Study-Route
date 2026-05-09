"""
loadtest.py — Phase 5C：并发负载测试

用途：模拟多个用户同时使用 LLM 服务，测量系统在负载下的表现。

和 benchmark.py 的区别：
  benchmark.py → 串行，一次一个，测"哪个 provider 快"
  loadtest.py  → 并发，多个同时发，测"这个服务能扛多少人"

核心指标：
  - 吞吐量（requests/s）—— 系统每秒能处理多少个请求
  - 延迟分布（P50 / P95 / P99）—— 大多数请求要等多久
  - 错误率 —— 负载上来后会不会开始报错
  - token/s —— 并发场景下的生成速度

用法：
    $env:DEEPSEEK_API_KEY = "sk-..."
    python loadtest.py --concurrency 5 --requests 20

    # 测本地 Ollama
    python loadtest.py --concurrency 3 --requests 10 --base-url http://localhost:11434/v1 --model qwen2.5:7b --api-key ollama

    # 测你的 gateway
    python loadtest.py --concurrency 5 --requests 20 --base-url http://localhost:8000/v1

依赖：
    pip install aiohttp
"""

import argparse
import asyncio
import json
import os
import statistics
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

try:
    import aiohttp
except ImportError:
    print("需要 aiohttp：pip install aiohttp", file=sys.stderr)
    raise


# =========================================================================
# 配置
# =========================================================================

DEFAULT_PROMPTS = {
    "short": "用一句话解释什么是缓存。",
    "medium": "请用三句话解释什么是 HTTP 协议，以及为什么它很重要。",
    "long": "请详细解释客户端-服务器架构的工作原理，包括请求-响应模型、无状态特性、以及常见的 HTTP 方法和状态码。",
}


@dataclass
class LoadTestConfig:
    base_url: str = "https://api.deepseek.com/v1"
    api_key: str = ""
    model: str = "deepseek-chat"
    concurrency: int = 5
    total_requests: int = 20
    prompt: str = DEFAULT_PROMPTS["short"]
    timeout: int = 120
    stream: bool = True


@dataclass
class RequestResult:
    """单个请求的结果"""
    success: bool
    first_token_ms: int | None = None
    total_ms: int = 0
    output_tokens: int = 0
    error: str | None = None


@dataclass
class LoadTestReport:
    """负载测试完整报告"""
    config: LoadTestConfig
    started_at: str = ""
    finished_at: str = ""
    duration_sec: float = 0
    total: int = 0
    success: int = 0
    failed: int = 0
    results: list[RequestResult] = field(default_factory=list)

    @property
    def success_rate_pct(self) -> float:
        return (self.success / self.total * 100) if self.total > 0 else 0

    @property
    def throughput(self) -> float:
        """吞吐量：每秒完成多少个请求"""
        return self.total / self.duration_sec if self.duration_sec > 0 else 0

    @property
    def latency_stats(self) -> dict[str, float]:
        """延迟分布"""
        first_tokens = [r.first_token_ms for r in self.results if r.success and r.first_token_ms]
        totals = [r.total_ms for r in self.results if r.success and r.total_ms > 0]
        return {
            "first_token": _latency_stats(first_tokens),
            "total": _latency_stats(totals),
        }

    @property
    def total_output_tokens(self) -> int:
        return sum(r.output_tokens for r in self.results if r.success)

    @property
    def tokens_per_second(self) -> float:
        return self.total_output_tokens / self.duration_sec if self.duration_sec > 0 else 0


def _latency_stats(data: list[int]) -> dict[str, float]:
    if not data:
        return {"avg": 0, "p50": 0, "p95": 0, "p99": 0, "min": 0, "max": 0}
    return {
        "avg": round(statistics.mean(data)),
        "p50": round(_percentile(data, 50)),
        "p95": round(_percentile(data, 95)),
        "p99": round(_percentile(data, 99)),
        "min": min(data),
        "max": max(data),
    }


def _percentile(data: list, pct: float) -> float:
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * pct / 100
    f = int(k)
    c = f + 1 if f + 1 < len(sorted_data) else f
    return sorted_data[f] * (c - k) + sorted_data[c] * (k - f)


# =========================================================================
# 核心：并发请求
# =========================================================================

async def _send_one(
    session: aiohttp.ClientSession,
    config: LoadTestConfig,
    worker_id: int,
) -> RequestResult:
    """发送一个流式请求，测量延迟。"""
    payload = {
        "model": config.model,
        "messages": [{"role": "user", "content": config.prompt}],
        "stream": config.stream,
        "temperature": 0.7,
        "max_tokens": 512,
    }
    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream" if config.stream else "application/json",
    }

    url = f"{config.base_url.rstrip('/')}/chat/completions"
    started_at = time.perf_counter()
    first_token_at = None
    output_tokens = 0

    try:
        async with session.post(
            url,
            json=payload,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=config.timeout),
        ) as response:
            if response.status != 200:
                body = await response.text()
                return RequestResult(
                    success=False,
                    total_ms=int((time.perf_counter() - started_at) * 1000),
                    error=f"HTTP {response.status}: {body[:200]}",
                )

            if config.stream:
                # 解析 SSE 流
                async for line in response.content:
                    text = line.decode("utf-8", errors="replace").strip()
                    if not text or not text.startswith("data:"):
                        continue
                    data_str = text.removeprefix("data:").strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue
                    delta = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                    if delta:
                        if first_token_at is None:
                            first_token_at = time.perf_counter()
                        output_tokens += 1
            else:
                body = await response.json()
                content = body.get("choices", [{}])[0].get("message", {}).get("content", "")
                output_tokens = body.get("usage", {}).get("completion_tokens", len(content))
                # 非流式没有 first_token 概念
                first_token_at = time.perf_counter()  # 收到完整响应的时间

        finished_at = time.perf_counter()
        first_token_ms = None
        if first_token_at is not None:
            first_token_ms = int((first_token_at - started_at) * 1000)

        return RequestResult(
            success=True,
            first_token_ms=first_token_ms,
            total_ms=int((finished_at - started_at) * 1000),
            output_tokens=output_tokens,
        )

    except asyncio.TimeoutError:
        return RequestResult(
            success=False,
            total_ms=int((time.perf_counter() - started_at) * 1000),
            error="timeout",
        )
    except Exception as exc:
        return RequestResult(
            success=False,
            total_ms=int((time.perf_counter() - started_at) * 1000),
            error=str(exc)[:200],
        )


async def _worker(
    worker_id: int,
    queue: asyncio.Queue,
    config: LoadTestConfig,
    results: list[RequestResult],
):
    """工作协程：从队列取任务，发送请求，记录结果。"""
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                task_id = queue.get_nowait()
            except asyncio.QueueEmpty:
                return

            result = await _send_one(session, config, worker_id)
            result.task_id = task_id  # type: ignore
            results.append(result)
            queue.task_done()


async def run_load_test(config: LoadTestConfig) -> LoadTestReport:
    """运行负载测试。"""
    report = LoadTestReport(config=config)
    report.started_at = datetime.now().isoformat()

    # 任务队列：每个请求一个任务
    queue: asyncio.Queue = asyncio.Queue()
    for i in range(config.total_requests):
        queue.put_nowait(i)

    results: list[RequestResult] = []

    t0 = time.perf_counter()

    # 启动并发 worker
    workers = [
        _worker(i, queue, config, results)
        for i in range(config.concurrency)
    ]
    await asyncio.gather(*workers)

    report.duration_sec = time.perf_counter() - t0
    report.total = len(results)
    report.success = sum(1 for r in results if r.success)
    report.failed = sum(1 for r in results if not r.success)
    report.results = results
    report.finished_at = datetime.now().isoformat()

    return report


# =========================================================================
# 报告输出
# =========================================================================

def print_report(report: LoadTestReport):
    """打印人类可读的测试报告。"""
    c = report.config
    ls_ft = report.latency_stats["first_token"]
    ls_tot = report.latency_stats["total"]

    print()
    print("=" * 60)
    print("  LLM 负载测试报告")
    print("=" * 60)
    print(f"  目标：    {c.base_url}")
    print(f"  模型：    {c.model}")
    print(f"  并发数：  {c.concurrency}")
    print(f"  总请求：  {c.total_requests}")
    print(f"  耗时：    {report.duration_sec:.1f}s")
    print()
    print(f"  成功：    {report.success} / {report.total}（{report.success_rate_pct:.1f}%）")
    print(f"  失败：    {report.failed}")
    print(f"  吞吐量：  {report.throughput:.2f} req/s")
    print(f"  总输出：  {report.total_output_tokens:,} tokens")
    print(f"  生成速度：{report.tokens_per_second:.1f} token/s")
    print()

    # 延迟分布表
    if ls_tot["avg"] > 0:
        print("  首 token 延迟（ms）：")
        print(f"    avg={ls_ft['avg']:.0f}  p50={ls_ft['p50']:.0f}  p95={ls_ft['p95']:.0f}  p99={ls_ft['p99']:.0f}")
        print(f"    min={ls_ft['min']:.0f}  max={ls_ft['max']:.0f}")
        print()
        print("  总耗时（ms）：")
        print(f"    avg={ls_tot['avg']:.0f}  p50={ls_tot['p50']:.0f}  p95={ls_tot['p95']:.0f}  p99={ls_tot['p99']:.0f}")
        print(f"    min={ls_tot['min']:.0f}  max={ls_tot['max']:.0f}")

    # 失败详情
    if report.failed > 0:
        print()
        print("  失败详情：")
        for r in report.results:
            if not r.success:
                print(f"    [{r.task_id}] {r.error}")  # type: ignore

    print("=" * 60)

    # 解读
    print()
    print("  怎么读这份报告：")
    print("  - P50 = 一半请求的延迟低于这个值（'典型'用户体验）")
    print("  - P95 = 95% 的请求延迟低于这个值（'最差'用户体验）")
    print("  - 如果 P95 远大于 P50 → 系统不稳定，部分请求被阻塞")
    print("  - 如果错误率 > 1% → 系统扛不住当前并发")


def save_report_json(report: LoadTestReport, path: str = "loadtest_report.json"):
    """保存机器可读的 JSON 报告。"""
    data = {
        "config": {
            "base_url": report.config.base_url,
            "model": report.config.model,
            "concurrency": report.config.concurrency,
            "total_requests": report.config.total_requests,
        },
        "started_at": report.started_at,
        "finished_at": report.finished_at,
        "duration_sec": report.duration_sec,
        "total": report.total,
        "success": report.success,
        "failed": report.failed,
        "success_rate_pct": report.success_rate_pct,
        "throughput_req_per_sec": report.throughput,
        "tokens_per_second": report.tokens_per_second,
        "latency_stats": report.latency_stats,
        "errors": [
            {"task_id": r.task_id, "error": r.error}  # type: ignore
            for r in report.results
            if not r.success
        ],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\nJSON 报告已保存到 {path}")


# =========================================================================
# CLI
# =========================================================================

def parse_args() -> LoadTestConfig:
    parser = argparse.ArgumentParser(
        description="LLM 并发负载测试工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python loadtest.py --concurrency 5 --requests 20
  python loadtest.py -c 10 -n 50 --prompt long
  python loadtest.py -c 3 -n 10 --base-url http://localhost:11434/v1 --model qwen2.5:7b --api-key ollama
        """,
    )
    parser.add_argument("-c", "--concurrency", type=int, default=5,
                        help="并发 worker 数（默认 5）")
    parser.add_argument("-n", "--requests", type=int, default=20,
                        help="总请求数（默认 20）")
    parser.add_argument("--base-url", default="https://api.deepseek.com/v1",
                        help="LLM API 地址")
    parser.add_argument("--model", default="deepseek-chat",
                        help="模型名")
    parser.add_argument("--api-key", default=None,
                        help="API Key（默认读 $env:DEEPSEEK_API_KEY）")
    parser.add_argument("--prompt", default="short",
                        help="测试 prompt：short / medium / long，或自定义文本")
    parser.add_argument("--timeout", type=int, default=120,
                        help="单个请求超时秒数")
    parser.add_argument("--no-stream", action="store_true",
                        help="关闭流式（默认开启）")
    parser.add_argument("--output", default=None,
                        help="保存 JSON 报告到指定路径")

    args = parser.parse_args()

    api_key = args.api_key or os.getenv("DEEPSEEK_API_KEY", "")
    if not api_key:
        print("警告：未设置 API Key。本地 Ollama 可以用 --api-key ollama", file=sys.stderr)

    prompt_text = DEFAULT_PROMPTS.get(args.prompt, args.prompt)

    return LoadTestConfig(
        base_url=args.base_url,
        api_key=api_key,
        model=args.model,
        concurrency=args.concurrency,
        total_requests=args.requests,
        prompt=prompt_text,
        timeout=args.timeout,
        stream=not args.no_stream,
    )


async def main():
    config = parse_args()

    print(f"开始负载测试...")
    print(f"  目标：{config.base_url}")
    print(f"  模型：{config.model}")
    print(f"  并发：{config.concurrency} worker, {config.total_requests} 请求")
    print(f"  Prompt：{config.prompt[:60]}...")
    print()

    report = await run_load_test(config)
    print_report(report)

    import argparse as _argparse
    args = _argparse.Namespace(**{"output": None})
    try:
        parsed = parse_args()
        args = parsed  # type: ignore
    except (SystemExit, Exception):
        pass

    output_path = getattr(args, "output", None) if hasattr(args, "output") else None  # type: ignore
    if output_path:
        save_report_json(report, output_path)


if __name__ == "__main__":
    asyncio.run(main())
