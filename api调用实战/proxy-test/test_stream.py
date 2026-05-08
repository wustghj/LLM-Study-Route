import json
import os
import time
import urllib.error
import urllib.request


BASE_URL = os.getenv("PROXY_BASE_URL", "http://localhost:3000/v1").rstrip("/")
API_KEY = os.getenv("PROXY_API_KEY", "test-key")
MODEL = os.getenv("PROXY_MODEL", "deepseek-chat")


def iter_sse_lines(response):
    """使用 readline 逐行读取 SSE 数据流，避免跨 TCP 段丢数据。"""
    for raw_line in response.readlines():
        line = raw_line.decode("utf-8", errors="replace").strip()
        if not line or not line.startswith("data:"):
            continue
        yield line.removeprefix("data:").strip()


def main() -> int:
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "你是一个简洁的技术助手。"},
            {"role": "user", "content": "用三句话解释流式响应为什么适合大模型对话。"},
        ],
        "stream": True,
        "temperature": 0.7,
        "max_tokens": 256,
    }

    request = urllib.request.Request(
        url=f"{BASE_URL}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
    )

    started_at = time.perf_counter()
    first_token_at = None

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            print("assistant:")
            for event in iter_sse_lines(response):
                if event == "[DONE]":
                    break

                data = json.loads(event)
                delta = data["choices"][0].get("delta", {}).get("content") or ""
                if not delta:
                    continue

                if first_token_at is None:
                    first_token_at = time.perf_counter()

                print(delta, end="", flush=True)
    except urllib.error.HTTPError as exc:
        print(f"\nHTTP {exc.code}")
        print(exc.read().decode("utf-8", errors="replace"))
        return 1
    except urllib.error.URLError as exc:
        print(f"\n请求失败：{exc}")
        return 1

    finished_at = time.perf_counter()
    first_token_ms = None
    if first_token_at is not None:
        first_token_ms = int((first_token_at - started_at) * 1000)
    total_ms = int((finished_at - started_at) * 1000)
    print(f"\n\n[metrics] first_token_ms={first_token_ms}, total_ms={total_ms}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
