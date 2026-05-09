"""
agent.py — 基于 Function Calling 的 Agent

核心流程：
  用户提问
    → 1. LLM 决定：直接回答，还是调用某个工具？
    → 2. 如果要调用工具 → 执行工具 → 把结果给 LLM
    → 3. LLM 根据工具结果决定下一步（继续调用工具？还是给出最终回答？）
    → 4. 直到 LLM 给出最终回答

这就是 Agent 的"思考→行动→观察"循环。

用法：
    $env:DEEPSEEK_API_KEY="sk-..."
    python agent.py

示例：
    > 计算 12345 × 6789 等于多少？
    > 对比 1024 和 2^10 的大小
    > 退出
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable

from openai import OpenAI

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


# =========================================================================
# 配置
# =========================================================================

DEFAULT_CONFIG = {
    "api_key": "$DEEPSEEK_API_KEY",
    "base_url": "https://api.deepseek.com",
    "model": "deepseek-chat",
}


def resolve_env(value: Any) -> Any:
    if isinstance(value, str) and value.startswith("$"):
        return os.getenv(value[1:], "")
    return value


def load_config() -> dict[str, str]:
    path = Path(__file__).parent.parent.parent / "phase1-api" / "cli-chat" / "config.toml"
    if not path.exists():
        return DEFAULT_CONFIG
    with path.open("rb") as f:
        cfg = tomllib.load(f)
    result = DEFAULT_CONFIG.copy()
    result.update(cfg)
    return {k: resolve_env(v) for k, v in result.items()}


# =========================================================================
# 工具定义（Tool Definitions）
# =========================================================================

# Agent 能调用的工具，用 JSON Schema 描述
# 大模型会根据这个描述决定调哪个工具、传什么参数

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "执行数学计算，支持加减乘除和幂运算",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "要计算的数学表达式，如 '12345 * 6789' 或 '2 ** 10'",
                    },
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "获取当前的日期和时间",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "列出指定目录下的文件和子目录",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "要列出的目录路径，默认为当前目录",
                    },
                },
            },
        },
    },
]


# =========================================================================
# 工具实现（Tool Implementations）
# =========================================================================

# 注意：这里是用 Python 函数实现工具逻辑。
# 大模型只负责"决定调用哪个工具"，不负责"执行"。
# 执行是我们在本地完成的。


def tool_calculator(expression: str) -> str:
    """执行数学计算"""
    try:
        # 安全地 eval 数学表达式
        # 注意：生产环境不要直接用 eval！这里用作 demo
        allowed = set("0123456789+-*/.()% ")
        if not all(c in allowed for c in expression):
            return "错误：表达式包含不允许的字符"

        result = eval(expression, {"__builtins__": {}}, {})
        return f"{expression} = {result}"
    except Exception as exc:
        return f"计算错误：{exc}"


def tool_get_current_time() -> str:
    """获取当前时间"""
    now = time.localtime()
    return time.strftime("%Y-%m-%d %H:%M:%S", now)


def tool_list_directory(path: str = ".") -> str:
    """列出目录内容"""
    try:
        p = Path(path)
        if not p.exists():
            return f"错误：目录 {path} 不存在"
        if not p.is_dir():
            return f"错误：{path} 不是目录"

        items = []
        for entry in sorted(p.iterdir()):
            prefix = "📁" if entry.is_dir() else "📄"
            size = ""
            if entry.is_file():
                size = f" ({entry.stat().st_size / 1024:.1f} KB)"
            items.append(f"{prefix} {entry.name}{size}")

        return "\n".join(items) if items else "(空目录)"
    except Exception as exc:
        return f"错误：{exc}"


# 工具名称到函数的映射
TOOL_MAP: dict[str, Callable[..., str]] = {
    "calculator": tool_calculator,
    "get_current_time": tool_get_current_time,
    "list_directory": tool_list_directory,
}


# =========================================================================
# Agent 循环
# =========================================================================

def run_agent_loop(
    client: OpenAI,
    model: str,
    messages: list[dict],
    max_turns: int = 10,
) -> list[dict]:
    """
    Agent 的核心循环：

    1. 把消息发给 LLM
    2. 如果 LLM 返回文本 → 结束（回答完成）
    3. 如果 LLM 返回 function_call → 执行对应的工具
    4. 把工具结果作为新消息发给 LLM
    5. 回到步骤 2（最多 max_turns 轮）
    """
    for turn in range(max_turns):
        print(f"\n[Agent 思考中... 第 {turn + 1} 轮]", flush=True)

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.3,
        )

        choice = response.choices[0]

        # Case 1: LLM 直接回答（没有 tool call）
        if choice.finish_reason == "stop":
            content = choice.message.content or ""
            messages.append({"role": "assistant", "content": content})
            print(f"\n[Agent] {content}")
            return messages

        # Case 2: LLM 要调用工具
        if choice.finish_reason == "tool_calls":
            tool_calls = choice.message.tool_calls

            # 先把 assistant 的 tool_calls 消息加入历史
            messages.append(choice.message)

            for tc in tool_calls:
                tool_name = tc.function.name
                try:
                    args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    args = {}

                # 执行工具
                func = TOOL_MAP.get(tool_name)
                if func is None:
                    result = f"错误：未知工具 {tool_name}"
                else:
                    print(f"  → 调用工具：{tool_name}({args})", end="", flush=True)
                    t0 = time.perf_counter()
                    result = func(**args)
                    elapsed = int((time.perf_counter() - t0) * 1000)
                    print(f" 执行完毕（{elapsed}ms）")

                # 把工具结果加回消息历史
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })

            # 继续循环，让 LLM 看工具结果
            continue

        # Case 3: 意外情况
        break

    print("\n[Agent] 达到最大思考轮数，强制结束。")
    return messages


# =========================================================================
# 命令行界面
# =========================================================================

def print_header():
    print("=" * 60)
    print("Agent 演示 — 基于 Function Calling 的智能助手")
    print("=" * 60)
    print("这个 Agent 可以使用以下工具：")
    for tool in TOOLS:
        name = tool["function"]["name"]
        desc = tool["function"]["description"]
        print(f"  🔧 {name} — {desc}")
    print()
    print("输入问题让 Agent 帮你解决，输入 /exit 退出")
    print("=" * 60)


def main():
    config = load_config()
    api_key = config.get("api_key", "")
    base_url = config["base_url"].rstrip("/")
    model = config.get("model", "deepseek-chat")

    if not api_key or api_key == "not-needed":
        print("错误：请设置 API Key")
        print("  $env:DEEPSEEK_API_KEY = 'sk-...'")
        return 1

    client = OpenAI(api_key=api_key, base_url=base_url)
    print_header()

    system_prompt = (
        "你是一个智能助手，可以使用工具来帮助用户解决问题。"
        "对于每个问题，先思考需要哪些工具，然后按步骤调用。"
        "一次调用一个工具，看到结果后再决定下一步。"
        "当你收集到足够信息后，给用户一个完整的回答。"
        "回答时使用中文，用普通人能理解的语言。"
    )

    messages = [{"role": "system", "content": system_prompt}]

    while True:
        try:
            user_input = input("\n你> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n退出。")
            break

        if not user_input:
            continue
        if user_input in ("/exit", "退出"):
            break

        messages.append({"role": "user", "content": user_input})
        messages = run_agent_loop(client, model, messages)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
