"""
实验公共模块 — 调用 Ollama API 测量性能指标。
"""

import time
import sys
import json
import urllib.request
import urllib.error


def measure_ollama(base_url: str, model: str, prompt: str,
                   max_tokens: int = 256) -> dict:
    """测量一次 Ollama 推理的性能指标。"""
    t0 = time.perf_counter()
    first_token_at = None
    output_tokens = 0

    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": "你是一个简洁的助手。"},
            {"role": "user", "content": prompt},
        ],
        "stream": True,
        "temperature": 0.7,
        "max_tokens": max_tokens,
    }).encode("utf-8")

    url = f"{base_url.rstrip('/')}/chat/completions"
    req = urllib.request.Request(
        url, data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer ollama",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            for line in resp:
                text = line.decode("utf-8", errors="replace").strip()
                if not text.startswith("data:"):
                    continue
                data_str = text.removeprefix("data:").strip()
                if data_str == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                except json.JSONDecodeError:
                    continue
                delta = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                if delta:
                    if first_token_at is None:
                        first_token_at = time.perf_counter()
                    output_tokens += 1
    except urllib.error.URLError as exc:
        return {"success": False, "error": str(exc.reason)}
    except Exception as exc:
        return {"success": False, "error": str(exc)}

    done_at = time.perf_counter()
    ft_ms = int((first_token_at - t0) * 1000) if first_token_at else None
    total_ms = int((done_at - t0) * 1000)
    tps = round(output_tokens / (total_ms / 1000), 2) if total_ms > 0 else 0

    return {
        "success": True,
        "first_token_ms": ft_ms,
        "total_ms": total_ms,
        "output_tokens": output_tokens,
        "tokens_per_sec": tps,
    }


TEST_PROMPT = "请用三句话解释什么是 KV Cache，每句不超过 20 个字。"
