import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from openai import OpenAI
from openai import (
    AuthenticationError,
    RateLimitError,
    APITimeoutError,
    APIConnectionError,
)

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


DEFAULT_CONFIG = {
    "api_key": "sk-dae11c7987c2480490de024667ba7a50",
    "base_url": "https://api.deepseek.com",
    "model": "deepseek-chat",
    "system_prompt": "你是一个简洁、可靠的编程助手。",
    "temperature": 0.7,
    "max_tokens": 2048,
}


def resolve_env(value: Any) -> Any:
    if isinstance(value, str) and value.startswith("$"):
        env_name = value[1:]
        val = os.getenv(env_name)
        if val is None:
            print(f"警告：环境变量 {env_name} 未设置。请设置后再运行。", file=sys.stderr)
            return ""
        return val
    return value


def load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        print(f"错误：配置文件 {path} 不存在。", file=sys.stderr)
        print(f"提示：请复制 config.example.toml 为 {path} 并编辑。", file=sys.stderr)
        return DEFAULT_CONFIG.copy()

    with path.open("rb") as f:
        user_config = tomllib.load(f)

    config = DEFAULT_CONFIG.copy()
    config.update(user_config)
    return {key: resolve_env(value) for key, value in config.items()}


def default_conversation_path() -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return Path("conversations") / f"{timestamp}.json"


def load_messages(path: Path, system_prompt: str) -> list[dict[str, str]]:
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    return [{"role": "system", "content": system_prompt}]


def save_messages(path: Path, messages: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)


def stream_chat(client: OpenAI, config: dict[str, Any], messages: list[dict[str, str]]) -> str:
    started_at = time.perf_counter()
    first_token_at: float | None = None
    answer_parts: list[str] = []

    stream = client.chat.completions.create(
        model=config["model"],
        messages=messages,
        stream=True,
        temperature=float(config["temperature"]),
        max_tokens=int(config["max_tokens"]),
    )

    for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        if not delta:
            continue

        if first_token_at is None:
            first_token_at = time.perf_counter()

        print(delta, end="", flush=True)
        answer_parts.append(delta)

    finished_at = time.perf_counter()
    print()

    first_token_ms = None
    if first_token_at is not None:
        first_token_ms = int((first_token_at - started_at) * 1000)

    total_ms = int((finished_at - started_at) * 1000)
    print(f"[metrics] first_token_ms={first_token_ms}, total_ms={total_ms}")
    return "".join(answer_parts)


def build_client(config: dict[str, Any]) -> OpenAI:
    api_key = config.get("api_key") or "not-needed"
    return OpenAI(api_key=api_key, base_url=config["base_url"])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="OpenAI-Compatible CLI chat client",
        epilog="""
内置命令（输入后回车）：
  /exit   保存并退出
  /save   手动保存当前会话
  /new    新建会话

环境变量：
  DEEPSEEK_API_KEY    DeepSeek API Key（推荐使用）
  OPENAI_API_KEY      OpenAI API Key
  PROXY_API_KEY       本地 Proxy API Key

示例：
  $env:DEEPSEEK_API_KEY="sk-..."
  python main.py --config config.toml

同类工具：
  raw_client.py  — 相同功能，但不使用 OpenAI SDK，手写 HTTP
  benchmark.py   — 多 provider 自动化性能对比测试
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--config", default="config.toml", help="TOML 配置文件路径")
    parser.add_argument("--conversation", default=None, help="对话历史 JSON 路径")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_config(Path(args.config))
    conversation_path = Path(args.conversation) if args.conversation else default_conversation_path()
    messages = load_messages(conversation_path, config["system_prompt"])
    client = build_client(config)

    print(f"model={config['model']}")
    print(f"base_url={config['base_url']}")
    print(f"conversation={conversation_path}")
    print("输入 /exit 退出，/save 手动保存，/new 清空当前会话。")

    while True:
        try:
            user_input = input("\n你> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n退出。")
            save_messages(conversation_path, messages)
            return 0

        if not user_input:
            continue
        if user_input == "/exit":
            save_messages(conversation_path, messages)
            return 0
        if user_input == "/save":
            save_messages(conversation_path, messages)
            print(f"已保存到 {conversation_path}")
            continue
        if user_input == "/new":
            messages = [{"role": "system", "content": config["system_prompt"]}]
            conversation_path = default_conversation_path()
            print(f"已新建会话：{conversation_path}")
            continue

        messages.append({"role": "user", "content": user_input})
        print("\nAI> ", end="", flush=True)

        try:
            answer = stream_chat(client, config, messages)
        except AuthenticationError:
            messages.pop()
            print("\n认证失败：API Key 无效。请检查环境变量或 config.toml 中的 api_key。", file=sys.stderr)
            continue
        except RateLimitError as exc:
            messages.pop()
            print(f"\n请求被限流：{exc}", file=sys.stderr)
            print("提示：请稍后再试，或检查 API 配额。", file=sys.stderr)
            continue
        except APITimeoutError:
            messages.pop()
            print("\n请求超时：网络连接可能不稳定，或模型响应时间过长。", file=sys.stderr)
            print("提示：可以重试，或检查网络连接。", file=sys.stderr)
            continue
        except APIConnectionError:
            messages.pop()
            print("\n网络连接失败：无法连接到 API 服务器。", file=sys.stderr)
            print("提示：请检查网络连接、base_url 是否正确、VPN/代理是否开启。", file=sys.stderr)
            continue
        except Exception as exc:
            messages.pop()
            save_messages(conversation_path, messages)
            print(f"\n请求失败：{exc}", file=sys.stderr)
            print("提示：已保存当前会话。输入 /exit 退出或重新输入。", file=sys.stderr)
            continue

        messages.append({"role": "assistant", "content": answer})
        save_messages(conversation_path, messages)


if __name__ == "__main__":
    raise SystemExit(main())
