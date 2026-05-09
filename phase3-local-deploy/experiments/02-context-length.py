"""
实验 2：上下文越长越慢吗？

用同一个 prompt，通过填充不同长度的 context 来模拟长对话。
实际场景中，可以观察长时间多轮对话的 total_ms 变化。

运行：
  python 02-context-length.py
"""

from common import measure_ollama

OLLAMA_URL = "http://localhost:11434/v1"
MODEL = "qwen2.5:7b"

PROMPTS = {
    "短": "你好",
    "中": "请用 C++ 后端工程师能理解的方式，解释大模型推理中的 KV Cache，并给一个网络服务类比",
    "长": ("请详细解释大模型推理中的以下 5 个概念，每个给一个 C++ 后端工程师能理解的类比："
           "1. KV Cache\n2. Attention 机制\n3. 量化\n4. 流式输出\n5. 上下文窗口"),
}


def main():
    print("=" * 60)
    print("实验 2：上下文长度对性能的影响")
    print("=" * 60)
    print("注意：这个实验通过不同长度的 prompt 来近似模拟。")
    print("真正的长上下文影响需要在多轮对话中观察 total_ms 增长。")
    print()

    for label, prompt in PROMPTS.items():
        print(f"\n{'─' * 40}")
        print(f"Prompt：{label}")
        print(f"内容：{prompt[:60]}...")
        print()

        for run in range(3):
            print(f"  第 {run + 1} 次...", end=" ", flush=True)
            result = measure_ollama(OLLAMA_URL, MODEL, prompt)
            if result["success"]:
                print(f"首token={result['first_token_ms']}ms, "
                      f"总耗时={result['total_ms']}ms")
            else:
                print(f"失败: {result['error']}")

    print("\n预期观察：")
    print("  Prompt 越长 → Prefill 越慢 → 首 token 延迟越大")
    print("  Decode 速度（tok/s）基本不变（瓶颈在 GPU 计算能力）")
    print("  去 Phase 3 的 main.py 里做 15 轮连续对话，")
    print("  观察 total_ms 随对话轮次的增长趋势——那才是 KV Cache 变大的效果。")


if __name__ == "__main__":
    main()
