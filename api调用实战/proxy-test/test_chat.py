import json
import os
import urllib.error
import urllib.request


BASE_URL = os.getenv("PROXY_BASE_URL", "http://localhost:3000/v1").rstrip("/")
API_KEY = os.getenv("PROXY_API_KEY", "test-key")
MODEL = os.getenv("PROXY_MODEL", "deepseek-chat")


def main() -> int:
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "你是一个简洁的技术助手。"},
            {"role": "user", "content": "用一句话解释 LLM proxy 的作用。"},
        ],
        "stream": False,
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

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        print(f"HTTP {exc.code}")
        print(exc.read().decode("utf-8", errors="replace"))
        return 1
    except urllib.error.URLError as exc:
        print(f"请求失败：{exc}")
        return 1

    data = json.loads(body)
    print(json.dumps(data, ensure_ascii=False, indent=2))

    content = data["choices"][0]["message"]["content"]
    print("\nassistant:")
    print(content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
