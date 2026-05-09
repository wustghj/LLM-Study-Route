"""
实验 3：量化等级对比

用不同量化等级的模型（Q2_K / Q4_K_M / Q8_0），
比较回答质量和延迟差异。

前提：需要有不同量化等级的 GGUF 文件。
如果你用 Ollama，ollama list 可以看到模型的量化信息。

运行：
  python 03-quantization.py
"""

from common import measure_ollama

OLLAMA_URL = "http://localhost:11434/v1"

MODELS = [
    ("qwen2.5:1.5b", "1.5B Q4_K_M（默认量化）"),
    ("qwen2.5:7b", "7B Q4_K_M（默认量化）"),
]

QUALITY_PROMPT = "请用三句话解释什么是注意力机制（Attention），每句不超过 20 个字。"


def main():
    print("=" * 60)
    print("实验 3：量化等级对回答质量的影响")
    print("=" * 60)
    print()

    for model, desc in MODELS:
        print(f"\n模型：{desc}")
        print("-" * 40)

        for run in range(2):
            print(f"  第 {run + 1} 次...")
            result = measure_ollama(OLLAMA_URL, model, QUALITY_PROMPT)
            if result["success"]:
                print(f"    首token={result['first_token_ms']}ms, "
                      f"总耗时={result['total_ms']}ms, "
                      f"{result['tokens_per_sec']} tok/s")
            else:
                print(f"    失败: {result['error']}")

    print("\n总结：")
    print("  Q2_K (3GB)  → 文件最小，但回答质量明显下降（可能胡说）")
    print("  Q4_K_M (4.5GB) → 甜点级别：体积和质量的最佳平衡")
    print("  Q8_0 (7.5GB) → 接近原版质量，但文件大了很多")
    print()
    print("  如果 Ollama 只有 Q4_K_M，可以在 Hugging Face 下载不同量化的 GGUF 文件")
    print("  然后用 llama.cpp 直接加载对比。")


if __name__ == "__main__":
    main()
