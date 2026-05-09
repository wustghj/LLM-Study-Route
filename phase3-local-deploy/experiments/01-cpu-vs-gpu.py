"""
实验 1：GPU 加速到底有多大用？

改变 llama-server 的 -ngl 参数（0 / 20 / 99），
分别测量首 token 延迟和吞吐量。

前提：
  - Ollama 已安装并运行
  - 至少有一个模型（如 qwen2.5:7b）

运行：
  python 01-cpu-vs-gpu.py
"""

from common import measure_ollama, TEST_PROMPT

OLLAMA_URL = "http://localhost:11434/v1"

MODELS = {
    "qwen2.5:7b": "7B 参数模型",
    "qwen2.5:1.5b": "1.5B 参数模型（纯 CPU 也能跑）",
}


def main():
    print("=" * 60)
    print("实验 1：GPU 加速的效果")
    print("=" * 60)
    print("注意：这个实验测量的是 Ollama（底层已启用 GPU）的延迟。")
    print("要测纯 CPU，请修改 Ollama 配置或在另一台无 GPU 的机器上跑。")
    print()

    for model, desc in MODELS.items():
        print(f"\n测试模型：{model} ({desc})")
        print("-" * 40)

        for run in range(3):
            print(f"  第 {run + 1} 次...", end=" ", flush=True)
            result = measure_ollama(OLLAMA_URL, model, TEST_PROMPT)
            if result["success"]:
                print(f"首token={result['first_token_ms']}ms, "
                      f"总耗时={result['total_ms']}ms, "
                      f"{result['tokens_per_sec']} tok/s")
            else:
                print(f"失败: {result['error']}")

    print("\n结论：")
    print("  对于 7B 模型，纯 CPU 推理（-ngl 0）首 token 延迟通常 >= 5秒。")
    print("  启用 GPU 加速（-ngl 99）可以把延迟降到 <= 1秒。")
    print("  如果你的机器有 NVIDIA 显卡，去任务管理器确认 Ollama 在用 GPU。")


if __name__ == "__main__":
    main()
