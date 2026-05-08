"""
cost.py — Phase 5B：成本追踪

用途：计算每次 LLM 调用的费用。支持多家 provider 的实时定价。

核心概念：
  - 输入 token：你发给模型的内容（包括 system prompt + 历史消息）
  - 输出 token：模型生成的内容
  - 缓存命中：部分 provider（如 DeepSeek）对重复前缀有折扣
  - 计费单位：通常按"每百万 token"计价

用法：
    from cost import CostTracker

    tracker = CostTracker()
    cost = tracker.calculate("deepseek-chat", input_tokens=500, output_tokens=1200)
    print(f"这次请求花了 CNY{cost['total']:.6f}")

依赖：无（纯标准库）
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class PriceInfo:
    """一个模型的价格信息"""
    input_price_per_m: float   # 每百万输入 token 的价格
    output_price_per_m: float  # 每百万输出 token 的价格
    currency: str              # CNY / USD
    cache_hit_discount: float = 0.0  # 缓存命中折扣（0=无折扣, 0.5=半价）


# =========================================================================
# 实时定价表
# 数据来源（2026-05）：
#   DeepSeek: https://platform.deepseek.com/api-docs/pricing
#   OpenAI:   https://openai.com/api/pricing/
# 注意：价格会变动，以官网为准。
# =========================================================================

PRICING: dict[str, dict[str, PriceInfo]] = {
    "deepseek": {
        "deepseek-chat":     PriceInfo(input_price_per_m=0.5,  output_price_per_m=2.0,  currency="CNY", cache_hit_discount=0.5),
        "deepseek-reasoner":  PriceInfo(input_price_per_m=1.0,  output_price_per_m=4.0,  currency="CNY", cache_hit_discount=0.5),
    },
    "openai": {
        "gpt-4o":            PriceInfo(input_price_per_m=2.5,  output_price_per_m=10.0, currency="USD"),
        "gpt-4o-mini":       PriceInfo(input_price_per_m=0.15, output_price_per_m=0.6,  currency="USD"),
        "gpt-4.1":           PriceInfo(input_price_per_m=2.0,  output_price_per_m=8.0,  currency="USD"),
    },
    # 本地模型免费
    "ollama": {
        "*":                  PriceInfo(input_price_per_m=0.0,  output_price_per_m=0.0,  currency="CNY"),
    },
}


class CostTracker:
    """成本计算器。支持多 provider 和多模型。"""

    def __init__(self, pricing: dict[str, dict[str, PriceInfo]] | None = None):
        self.pricing = pricing or PRICING
        self._history: list[dict[str, Any]] = []  # 本地成本历史

    def calculate(
        self,
        model: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cache_hit_tokens: int = 0,
        provider: str | None = None,
    ) -> dict[str, Any]:
        """
        计算一次请求的费用。

        参数：
          - model: 模型名（如 "deepseek-chat", "gpt-4o-mini"）
          - input_tokens: 输入 token 数
          - output_tokens: 输出 token 数
          - cache_hit_tokens: 缓存命中的 token 数（DeepSeek 支持）
          - provider: 如果没传，自动根据 model 名猜

        返回：
          {"input_cost": ..., "output_cost": ..., "cache_discount": ..., "total": ..., "currency": ..., "model": ...}
        """
        # 1. 查价格
        price = self._find_price(model, provider)
        if price is None:
            return {
                "input_cost": 0, "output_cost": 0, "total": 0,
                "currency": "?", "model": model,
                "note": f"未找到 {model} 的价格信息"
            }

        # 2. 计算
        input_cost = (input_tokens / 1_000_000) * price.input_price_per_m
        output_cost = (output_tokens / 1_000_000) * price.output_price_per_m

        # 缓存命中折扣
        cache_discount = 0.0
        if cache_hit_tokens > 0 and price.cache_hit_discount > 0:
            normal_input = input_tokens - cache_hit_tokens
            cached_cost = (cache_hit_tokens / 1_000_000) * price.input_price_per_m * (1 - price.cache_hit_discount)
            input_cost = (normal_input / 1_000_000) * price.input_price_per_m + cached_cost
            cache_discount = (cache_hit_tokens / 1_000_000) * price.input_price_per_m * price.cache_hit_discount

        total = input_cost + output_cost

        result = {
            "model": model,
            "provider": self._guess_provider(model, provider),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cache_hit_tokens": cache_hit_tokens,
            "input_cost": round(input_cost, 8),
            "output_cost": round(output_cost, 8),
            "cache_discount": round(cache_discount, 8),
            "total": round(total, 8),
            "currency": price.currency,
            "unit": f"{price.currency}/M tokens",
        }

        self._history.append(result)
        return result

    def _find_price(self, model: str, provider: str | None = None) -> PriceInfo | None:
        """查价格表。"""
        # 先按 provider 查
        if provider and provider in self.pricing:
            if model in self.pricing[provider]:
                return self.pricing[provider][model]
            if "*" in self.pricing[provider]:
                return self.pricing[provider]["*"]

        # 再全局搜
        for p_name, models in self.pricing.items():
            if model in models:
                return models[model]
            if "*" in models:
                return models["*"]

        return None

    def _guess_provider(self, model: str, provider: str | None = None) -> str:
        if provider:
            return provider
        for p_name, models in self.pricing.items():
            if model in models:
                return p_name
        return "unknown"

    @property
    def history(self) -> list[dict[str, Any]]:
        return self._history

    def total_cost(self) -> dict[str, Any]:
        """返回历史总费用摘要。"""
        if not self._history:
            return {"total_requests": 0, "total_cost": 0}

        return {
            "total_requests": len(self._history),
            "total_input_tokens": sum(r["input_tokens"] for r in self._history),
            "total_output_tokens": sum(r["output_tokens"] for r in self._history),
            "by_currency": _aggregate_by_currency(self._history),
            "by_model": _aggregate_by_model(self._history),
        }


def _aggregate_by_currency(history: list[dict]) -> dict[str, float]:
    result: dict[str, float] = {}
    for r in history:
        c = r["currency"]
        result[c] = result.get(c, 0) + r["total"]
    return {k: round(v, 8) for k, v in result.items()}


def _aggregate_by_model(history: list[dict]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for r in history:
        m = r["model"]
        if m not in result:
            result[m] = {"count": 0, "total_cost": 0, "currency": r["currency"]}
        result[m]["count"] += 1
        result[m]["total_cost"] = round(result[m]["total_cost"] + r["total"], 8)
    return result


# =========================================================================
# 命令行工具：给定 token 数，显示费用
# =========================================================================
def demo():
    print("Phase 5B — 成本追踪演示\n")

    tracker = CostTracker()

    examples = [
        # 日常短对话
        ("deepseek-chat", 150, 300, 0),
        # 长对话（含大量上下文）
        ("deepseek-chat", 4000, 800, 0),
        # DeepSeek 缓存命中（system prompt 不变 → 大部分输入命中缓存）
        ("deepseek-chat", 4000, 800, 3800),
        # GPT-4o 长回答
        ("gpt-4o", 500, 2000, 0),
        # GPT-4o-mini（便宜）
        ("gpt-4o-mini", 500, 2000, 0),
        # 本地模型
        ("qwen2.5:7b", 500, 1200, 0),
    ]

    print(f"{'模型':<22s} {'输入':>8s} {'输出':>8s} {'缓存':>8s} {'输入费':>10s} {'输出费':>10s} {'总计':>12s} {'币种':>5s}")
    print("-" * 90)

    for model, inp, out, cache in examples:
        r = tracker.calculate(model, input_tokens=inp, output_tokens=out, cache_hit_tokens=cache)
        currency = r["currency"]
        print(f"{model:<22s} {inp:>6,}  {out:>6,}  {cache:>6,}  "
              f"{r['input_cost']:>8.6f}{currency} {r['output_cost']:>8.6f}{currency} "
              f"{r['total']:>10.6f}{currency} {currency:>5s}")

    # 累计
    print()
    summary = tracker.total_cost()
    print(f"总请求数：{summary['total_requests']}")
    print(f"总输入 token：{summary['total_input_tokens']:,}")
    print(f"总输出 token：{summary['total_output_tokens']:,}")
    for c, total in summary["by_currency"].items():
        print(f"总费用（{c}）：{total:.6f}")

    # 降本提示
    print()
    print("降本技巧：")
    print("  1. 把 system prompt 放前面 → DeepSeek 缓存命中，输入费减半")
    print("  2. 用 gpt-4o-mini 代替 gpt-4o 做简单任务（便宜 10-40 倍）")
    print("  3. 敏感数据/高并发 → 本地模型（完全免费）")
    print("  4. 缩短 system prompt 和上下文 → 每次请求都省钱")


if __name__ == "__main__":
    demo()
