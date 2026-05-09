"""
logger.py — Phase 5A：结构化 JSON 日志

用途：给你的 LLM 客户端加上生产级日志。每次请求记录一行 JSON。
print() 是给人看的，JSON 日志是给工具分析的。

格式：JSON Lines（每行一个 JSON 对象）
好处：可以 grep、jq、导入 Pandas、喂给日志平台

用法：
    from logger import RequestLogger

    logger = RequestLogger("logs/llm_requests.jsonl")
    logger.log(
        model="deepseek-chat",
        provider="deepseek",
        input_tokens=150,
        output_tokens=300,
        first_token_ms=320,
        total_ms=4200,
        status="success",
        cost=0.00075,
    )

    # 读取日志
    logs = logger.read_logs()
    summary = logger.summary()

依赖：无（纯标准库）
"""

import json
import os
import statistics
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class RequestLogger:
    """将每次 LLM 请求记录为一行 JSON。"""

    def __init__(self, log_path: str = "logs/llm_requests.jsonl"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log(
        self,
        *,
        model: str,
        provider: str = "unknown",
        base_url: str = "",
        input_tokens: int = 0,
        output_tokens: int = 0,
        first_token_ms: int | None = None,
        total_ms: int = 0,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        status: str = "success",
        error_type: str | None = None,
        cost: float = 0.0,
        user_message_preview: str = "",
    ) -> dict[str, Any]:
        """记录一次请求。返回记录对象。"""
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": uuid.uuid4().hex[:12],
            "model": model,
            "provider": provider,
            "base_url": base_url,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "first_token_ms": first_token_ms,
            "total_ms": total_ms,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "status": status,  # success / error
            "error_type": error_type,
            "cost": round(cost, 6),
            "user_message_preview": user_message_preview[:80],
        }

        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        return record

    def read_logs(self, limit: int = 0) -> list[dict[str, Any]]:
        """读取所有日志。limit=0 表示全部。"""
        if not self.log_path.exists():
            return []

        logs = []
        with self.log_path.open("r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if limit and i >= limit:
                    break
                line = line.strip()
                if line:
                    try:
                        logs.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return logs

    def summary(self) -> dict[str, Any]:
        """生成日志摘要：总请求数、错误率、延迟分布、费用汇总。"""
        logs = self.read_logs()
        if not logs:
            return {"message": "还没有日志记录"}

        total = len(logs)
        errors = [r for r in logs if r["status"] != "success"]
        error_rate = len(errors) / total * 100

        # token 统计
        total_input = sum(r.get("input_tokens", 0) for r in logs)
        total_output = sum(r.get("output_tokens", 0) for r in logs)
        total_cost = sum(r.get("cost", 0) for r in logs)

        # 延迟统计（仅成功请求）
        success_logs = [r for r in logs if r["status"] == "success"]
        first_tokens = [r["first_token_ms"] for r in success_logs if r.get("first_token_ms")]
        totals = [r["total_ms"] for r in success_logs if r.get("total_ms")]

        # 按 provider 分组
        by_provider: dict[str, dict[str, Any]] = {}
        for r in logs:
            p = r.get("provider", "unknown")
            if p not in by_provider:
                by_provider[p] = {"count": 0, "errors": 0, "total_cost": 0, "latencies": []}
            by_provider[p]["count"] += 1
            if r["status"] != "success":
                by_provider[p]["errors"] += 1
            by_provider[p]["total_cost"] += r.get("cost", 0)
            if r.get("total_ms"):
                by_provider[p]["latencies"].append(r["total_ms"])

        return {
            "total_requests": total,
            "errors": len(errors),
            "error_rate_pct": round(error_rate, 2),
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_cost": round(total_cost, 6),
            "avg_first_token_ms": round(statistics.mean(first_tokens)) if first_tokens else None,
            "avg_total_ms": round(statistics.mean(totals)) if totals else None,
            "p95_total_ms": _percentile(totals, 95) if totals else None,
            "by_provider": {
                p: {
                    **stats,
                    "avg_latency_ms": round(statistics.mean(stats["latencies"])) if stats["latencies"] else None,
                }
                for p, stats in by_provider.items()
            },
        }


def _percentile(data: list[float], pct: float) -> float:
    """计算百分位数（无 numpy 依赖）。"""
    if not data:
        return 0
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * pct / 100
    f = int(k)
    c = f + 1 if f + 1 < len(sorted_data) else f
    d0 = sorted_data[f] * (c - k)
    d1 = sorted_data[c] * (k - f)
    return d0 + d1


def log_to_summary_table(summary: dict) -> str:
    """把 summary 结果格式化成可打印的表格。"""
    if "message" in summary:
        return summary["message"]

    lines = [
        "=" * 55,
        "LLM 请求日志摘要",
        "=" * 55,
        f"总请求数：{summary['total_requests']}",
        f"错误率：  {summary['error_rate_pct']}%（{summary['errors']} 次）",
        f"总输入 token：{summary['total_input_tokens']:,}",
        f"总输出 token：{summary['total_output_tokens']:,}",
        f"总花费：  CNY{summary['total_cost']:.4f}",
        "",
        "延迟：",
        f"  平均首 token：{summary['avg_first_token_ms']}ms",
        f"  平均总耗时：  {summary['avg_total_ms']}ms",
        f"  P95 总耗时：  {summary['p95_total_ms']}ms",
        "",
        "按 Provider：",
    ]

    for provider, stats in summary.get("by_provider", {}).items():
        lines.append(
            f"  {provider}: {stats['count']} 请求, "
            f"{stats['errors']} 错误, "
            f"avg {stats['avg_latency_ms']}ms, "
            f"CNY{stats['total_cost']:.4f}"
        )

    lines.append("=" * 55)
    return "\n".join(lines)


# =========================================================================
# Demo：生成一些模拟日志，演示日志读写的完整流程
# =========================================================================
def demo():
    print("Phase 5A — 结构化日志演示\n")

    logger = RequestLogger("logs/demo_requests.jsonl")

    # 模拟几次请求
    scenarios = [
        {"model": "deepseek-chat", "provider": "deepseek", "input_tokens": 120, "output_tokens": 350, "first_token_ms": 310, "total_ms": 4200, "cost": 0.00076, "status": "success"},
        {"model": "qwen2.5:7b",    "provider": "ollama",   "input_tokens": 120, "output_tokens": 280, "first_token_ms": 5800, "total_ms": 28500, "cost": 0.0, "status": "success"},
        {"model": "deepseek-chat", "provider": "deepseek", "input_tokens": 85,  "output_tokens": 410, "first_token_ms": 290, "total_ms": 3900, "cost": 0.00086, "status": "success"},
        {"model": "deepseek-chat", "provider": "deepseek", "input_tokens": 200, "output_tokens": 0,   "first_token_ms": None, "total_ms": 0, "cost": 0.0, "status": "error", "error_type": "rate_limit"},
        {"model": "gpt-4o-mini",   "provider": "openai",   "input_tokens": 95,  "output_tokens": 520, "first_token_ms": 450, "total_ms": 5100, "cost": 0.00032, "status": "success"},
    ]

    for s in scenarios:
        record = logger.log(**s)
        status_icon = "[OK]" if s["status"] == "success" else "[ER]"
        print(f"  {status_icon} {record['request_id']}  {s['provider']:10s}  {s['model']:20s}  {s.get('total_ms', 0):>6}ms  CNY{s['cost']:.6f}")

    # 分析日志
    print()
    summary = logger.summary()
    print(log_to_summary_table(summary))

    # 清理演示日志
    logger.log_path.unlink(missing_ok=True)
    logger.log_path.parent.rmdir()  # 如果为空则删除
    try:
        logger.log_path.parent.rmdir()
    except OSError:
        pass


if __name__ == "__main__":
    demo()
