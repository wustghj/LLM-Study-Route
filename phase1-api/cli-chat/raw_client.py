"""
raw_client.py — 纯 HTTP 客户端（不依赖 OpenAI SDK）

用途：让你看到 API 请求的原始模样，理解 SDK 帮你做了什么。
和 main.py 完全一样的功能，但用标准库 urllib 手写 HTTP 请求。

用法：
    $env:DEEPSEEK_API_KEY="sk-..."
    python raw_client.py --config config.toml

和 main.py 的区别：
    main.py        → 用 OpenAI SDK，自动处理重试、超时、消息序列化
    raw_client.py  → 手写 HTTP，让你看到请求体和响应体的原始格式
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


DEFAULT_CONFIG = {
    "api_key": "$DEEPSEEK_API_KEY",
    "base_url": "https://api.deepseek.com",
    "model": "deepseek-chat",
    "system_prompt": "你是一个简洁、可靠的编程助手。",
    "temperature": 0.7,
    "max_tokens": 2048,
}


def resolve_env(value: Any) -> Any:
    if isinstance(value, str) and value.startswith("$"):
        val = os.getenv(value[1:])
        if val is None:
            print(f"警告：环境变量 {value[1:]} 未设置。", file=sys.stderr)
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


# =========================================================================
# 核心：手写 HTTP 请求，自己解析 SSE
# =========================================================================

def build_headers(api_key: str) -> dict[str, str]:
    """构建 HTTP 请求头"""
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",       # 告诉服务器我们要流式响应
    }


def build_body(
    model: str,
    messages: list[dict[str, str]],
    temperature: float,
    max_tokens: int,
    stream: bool = True,
) -> bytes:
    """构建 HTTP 请求体（JSON 序列化）"""
    payload = {
        "model": model,
        "messages": messages,
        "stream": stream,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


def iter_sse_lines(response):
    """
    逐行读取 SSE 数据流。
    用 readlines() 确保不会因为 TCP 分包而读到不完整的行。
    """
    for raw_line in response.readlines():
        line = raw_line.decode("utf-8", errors="replace").strip()
        if not line or not line.startswith("data:"):
            continue
        yield line.removeprefix("data:").strip()


def stream_chat_raw(
    config: dict[str, Any],
    messages: list[dict[str, str]],
) -> str:
    """
    纯 HTTP 流式对话。

    这里没有 SDK，你自己看着请求怎么发、响应怎么收。
    和 main.py 的 stream_chat 对比着看：
    - main.py:      client.chat.completions.create(stream=True)
    - raw_client:    urllib.request.Request + 手动解析 SSE
    """
    api_key = config.get("api_key") or "not-needed"
    base_url = config["base_url"].rstrip("/")
    model = config["model"]
    temperature = float(config["temperature"])
    max_tokens = int(config["max_tokens"])

    url = f"{base_url}/chat/completions"
    headers = build_headers(api_key)
    body = build_body(model, messages, temperature, max_tokens)

    # --- 打印请求信息，方便 debug ---
    print(f"[HTTP] POST {url}", file=sys.stderr)
    print(f"[HTTP] model={model}, temperature={temperature}, max_tokens={max_tokens}", file=sys.stderr)

    request = urllib.request.Request(
        url=url,
        data=body,
        method="POST",
        headers=headers,
    )

    started_at = time.perf_counter()
    first_token_at: float | None = None
    answer_parts: list[str] = []

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            print(f"[HTTP] 状态码: {response.status}", file=sys.stderr)
            print(file=sys.stderr)

            for event in iter_sse_lines(response):
                # SSE 终止符
                if event == "[DONE]":
                    break

                # 解析 JSON chunk
                try:
                    data = json.loads(event)
                except json.JSONDecodeError:
                    continue

                # 提取 delta content
                delta = (
                    data.get("choices", [{}])[0]
                    .get("delta", {})
                    .get("content", "")
                )
                if not delta:
                    continue

                if first_token_at is None:
                    first_token_at = time.perf_counter()

                print(delta, end="", flush=True)
                answer_parts.append(delta)

    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        print(f"\n[HTTP 错误] {exc.code}", file=sys.stderr)
        print(error_body[:300], file=sys.stderr)

        # 友好的错误提示
        if exc.code == 401:
            print("提示：API Key 无效，请检查环境变量或 config.toml。", file=sys.stderr)
        elif exc.code == 429:
            print("提示：请求太频繁，被限流了。请稍后再试。", file=sys.stderr)
        elif exc.code == 400:
            print("提示：请求参数有误，可能是 model 名称不对。", file=sys.stderr)
        raise

    except urllib.error.URLError as exc:
        print(f"\n[网络错误] {exc.reason}", file=sys.stderr)
        print("提示：无法连接到服务器，请检查网络和 base_url。", file=sys.stderr)
        raise

    finished_at = time.perf_counter()
    print()

    # --- 打印性能指标 ---
    first_token_ms = None
    if first_token_at is not None:
        first_token_ms = int((first_token_at - started_at) * 1000)
    total_ms = int((finished_at - started_at) * 1000)
    print(f"[metrics] first_token_ms={first_token_ms}, total_ms={total_ms}")
    print(f"[metrics] 提示：对比 main.py 相同的 prompt 和 model，这两个值应该一致")

    return "".join(answer_parts)


# =========================================================================
# 命令行界面
# =========================================================================

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Raw HTTP 版 CLI 聊天客户端（不依赖 OpenAI SDK）",
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
  python raw_client.py --config config.toml

对比 main.py：
  main.py 使用 OpenAI SDK，自动处理细节
  raw_client.py 手写 HTTP，让你看到协议层
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--config", default="config.toml", help="TOML 配置文件路径")
    parser.add_argument("--conversation", default=None, help="对话历史 JSON 路径")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_config(Path(args.config))
    conversation_path = (
        Path(args.conversation) if args.conversation
        else default_conversation_path()
    )
    messages = load_messages(conversation_path, config["system_prompt"])

    print(f"model  = {config['model']}")
    print(f"url    = {config['base_url']}/chat/completions")
    print(f"file   = {conversation_path}")
    print(f"sdk    = 无（纯 HTTP，手写 urllib）")
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
            answer = stream_chat_raw(config, messages)
        except Exception:
            messages.pop()
            continue

        messages.append({"role": "assistant", "content": answer})
        save_messages(conversation_path, messages)


if __name__ == "__main__":
    raise SystemExit(main())
