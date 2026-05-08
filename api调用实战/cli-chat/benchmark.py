"""
benchmark.py — 多 provider 自动性能对比

用法：
    python benchmark.py                    # 测试所有启用的 provider
    python benchmark.py --runs 3           # 每个 provider 测 3 次取平均
    python benchmark.py --output result.csv # 指定输出文件

输出：
    - CSV 文件，可用 Excel/WPS 打开画图
    - 每次追加，多次运行结果会自动累积

依赖：openai, tomli（和 main.py 一样）
"""

import csv
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from openai import OpenAI

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


# ---------- 默认配置（和 main.py 保持一致） ----------

DEFAULT_CONFIG = {
    "api_key": "$DEEPSEEK_API_KEY",
    "base_url": "https://api.deepseek.com",
    "model": "deepseek-chat",
}


def resolve_env(value: Any) -> Any:
    """将 $ENV_VAR 替换为环境变量值"""
    if isinstance(value, str) and value.startswith("$"):
        return os.getenv(value[1:], "")
    return value


def load_providers(toml_path: str = "config.toml") -> list[dict[str, str]]:
    """
    从 config.toml 读取所有注释掉的 provider 配置，
    以及当前启用的 provider。
    """
    path = Path(toml_path)
    if not path.exists():
        print(f"错误：找不到配置文件 {toml_path}")
        print("请先在 cli-chat/ 目录下运行此脚本")
        sys.exit(1)

    with path.open("rb") as f:
        raw = f.read().decode("utf-8")

    # 手动解析 TOML 以获取被注释的 provider 块
    # 格式：注释掉的配置以 # 开头
    lines = raw.split("\n")
    providers = []
    current = {}
    in_block = False

    for line in lines:
        stripped = line.strip()

        # 检测 provider 标题行（# DeepSeek, # OpenAI, 等）
        if stripped.startswith("# ") and not "=" in stripped:
            if current.get("name"):
                current = {}
            current["name"] = stripped.lstrip("# ").strip()
            in_block = False
            continue

        # 跳过注释说明行
        if stripped.startswith("# ") and "设置环境变量" in stripped:
            continue
        if stripped.startswith("# 使用前请复制"):
            continue

        # 解析 key = value（可能带 # 注释）
        if "=" in stripped:
            is_commented = stripped.startswith("# ")
            clean = stripped.lstrip("# ").strip()

            # 跳过非配置行
            if clean.startswith("#"):
                continue

            parts = clean.split("=", 1)
            key = parts[0].strip()
            value = parts[1].strip().strip('"').strip("'")

            if key == "api_key":
                current["api_key"] = resolve_env(value)
                current["api_key_raw"] = value
                current["commented"] = is_commented
            elif key == "base_url":
                current["base_url"] = value.rstrip("/")
            elif key == "model":
                current["model"] = value

    # 把启用的 provider 和注释的 provider 都收集起来
    result = []
    seen = set()
    # 需要测试的 provider 列表：当前启用的 + 所有注释的候选
    candidates = []

    # 从 DEFAULT_CONFIG 开始（当前启用的）
    default_api_key = resolve_env(DEFAULT_CONFIG["api_key"])
    if default_api_key:
        candidates.append({
            "name": "DeepSeek（当前）",
            "api_key": default_api_key,
            "base_url": DEFAULT_CONFIG["base_url"],
            "model": DEFAULT_CONFIG["model"],
        })

    # 从 config.toml 解析出来的候选
    # 为了简化，我们直接定义常见的 provider 组合
    provider_defs = [
        ("DeepSeek（云 API）", "$DEEPSEEK_API_KEY", "https://api.deepseek.com", "deepseek-chat"),
        ("Ollama（本地）", "ollama", "http://localhost:11434/v1", "qwen2.5:7b"),
        ("Proxy（本地）", "$PROXY_API_KEY", "http://localhost:3000/v1", "deepseek-chat"),
    ]

    for name, key_raw, base_url, model in provider_defs:
        key = resolve_env(key_raw)
        if key and key != "not-needed":
            candidates.append({
                "name": name,
                "api_key": key,
                "base_url": base_url,
                "model": model,
            })

    # 去重
    seen_urls = set()
    for c in candidates:
        key = (c["base_url"], c["model"])
        if key not in seen_urls:
            seen_urls.add(key)
            result.append(c)

    return result


TEST_PROMPTS = {
    "short": "用一句话解释什么是 KV Cache。",
    "medium": "请用 C++ 高性能后端工程师能理解的方式，解释大模型推理中的 KV Cache，并给一个网络服务类比。",
    "long": "请详细解释大模型推理中的以下概念，每个概念给一个 C++ 后端工程师能理解的类比：\n"
            "1. KV Cache\n2. Attention 机制\n3. 量化\n4. 流式输出\n5. 上下文窗口",
}


def test_provider(
    client: OpenAI,
    model: str,
    prompt: str,
    max_tokens: int = 512,
) -> dict[str, Any]:
    """测试一个 provider，返回性能指标"""
    messages = [
        {"role": "system", "content": "你是一个简洁、可靠的编程助手。"},
        {"role": "user", "content": prompt},
    ]

    started_at = time.perf_counter()
    first_token_at: float | None = None
    output_tokens = 0

    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True,
        temperature=0.7,
        max_tokens=max_tokens,
    )

    for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        if not delta:
            continue
        if first_token_at is None:
            first_token_at = time.perf_counter()
        output_tokens += 1

    finished_at = time.perf_counter()

    first_token_ms = None
    if first_token_at is not None:
        first_token_ms = int((first_token_at - started_at) * 1000)

    total_ms = int((finished_at - started_at) * 1000)
    tokens_per_sec = round(output_tokens / (total_ms / 1000), 2) if total_ms > 0 else 0

    return {
        "first_token_ms": first_token_ms,
        "total_ms": total_ms,
        "output_tokens": output_tokens,
        "tokens_per_sec": tokens_per_sec,
        "success": True,
        "error": None,
    }


def test_provider_safe(
    provider: dict[str, str],
    prompt: str,
    max_tokens: int = 512,
    timeout: int = 120,
) -> dict[str, Any]:
    """安全地测试一个 provider，捕获异常"""
    try:
        client = OpenAI(
            api_key=provider["api_key"],
            base_url=provider["base_url"],
            timeout=timeout,
        )
        result = test_provider(client, provider["model"], prompt, max_tokens)
        result["provider"] = provider["name"]
        result["base_url"] = provider["base_url"]
        result["model"] = provider["model"]
        return result
    except Exception as exc:
        return {
            "provider": provider["name"],
            "base_url": provider["base_url"],
            "model": provider["model"],
            "success": False,
            "error": str(exc),
            "first_token_ms": None,
            "total_ms": None,
            "output_tokens": 0,
            "tokens_per_sec": 0,
        }


def save_csv(results: list[dict[str, Any]], path: str = "benchmark.csv"):
    """将结果追加到 CSV 文件"""
    file_exists = os.path.isfile(path)
    fieldnames = [
        "timestamp", "provider", "base_url", "model",
        "prompt_type", "first_token_ms", "total_ms",
        "output_tokens", "tokens_per_sec", "success", "error",
    ]

    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerows(results)

    abs_path = os.path.abspath(path)
    print(f"\n📊 结果已追加到 {abs_path}")


def print_table(results: list[dict[str, Any]]):
    """终端打印结果表格"""
    print("\n" + "=" * 80)
    print(f"{'Provider':<25} {'首 token(ms)':<15} {'总耗时(ms)':<15} {'token/s':<10} {'状态':<10}")
    print("-" * 80)
    for r in results:
        if r["success"]:
            ft = str(r["first_token_ms"]) if r["first_token_ms"] else "-"
            print(
                f"{r['provider']:<25} {ft:<15} "
                f"{r['total_ms']:<15} {r['tokens_per_sec']:<10} ✅"
            )
        else:
            print(f"{r['provider']:<25} {'-':<15} {'-':<15} {'-':<10} ❌ {r['error'][:40]}")
    print("=" * 80)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="LLM Provider Benchmark")
    parser.add_argument("--config", default="config.toml", help="TOML 配置文件路径")
    parser.add_argument("--runs", type=int, default=1, help="每个 provider 测试次数（默认 1）")
    parser.add_argument("--output", default="benchmark.csv", help="CSV 输出文件")
    parser.add_argument("--prompt", choices=["short", "medium", "long"], default="short",
                        help="测试 prompt 长度（默认 short，避免花太多 token 钱）")
    args = parser.parse_args()

    # 切换到 cli-chat 目录
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    print(f"🔍 正在检测可用的 provider...")
    providers = load_providers(args.config)

    if not providers:
        print("未检测到可用的 provider。请确保设置了至少一个 API Key。")
        print("  DeepSeek: $env:DEEPSEEK_API_KEY='sk-...'")
        print("  OpenAI:   $env:OPENAI_API_KEY='sk-...'")
        print("  Proxy:    $env:PROXY_API_KEY='test-key'")
        return 1

    print(f"找到 {len(providers)} 个 provider：")
    for p in providers:
        print(f"  • {p['name']:25s} → {p['base_url']}")
    print()

    prompt_text = TEST_PROMPTS[args.prompt]
    print(f"测试 prompt（{args.prompt}）：{prompt_text[:60]}...")
    print(f"每个 provider 测试 {args.runs} 次")
    print()

    all_results = []
    for run_idx in range(args.runs):
        if args.runs > 1:
            print(f"\n--- 第 {run_idx + 1}/{args.runs} 轮 ---")
        for provider in providers:
            print(f"  测试 {provider['name']}... ", end="", flush=True)
            result = test_provider_safe(provider, prompt_text)

            # 补充元数据
            result["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            result["prompt_type"] = args.prompt
            result["run"] = run_idx + 1
            all_results.append(result)

            if result["success"]:
                print(f"首 token {result['first_token_ms']}ms, 总耗时 {result['total_ms']}ms, {result['tokens_per_sec']} token/s")
            else:
                print(f"❌ {result['error'][:60]}")

    # 输出
    print_table(all_results)
    save_csv(all_results, args.output)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
