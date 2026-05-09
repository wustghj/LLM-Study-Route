"""Visualize KV Cache size growth with context length."""


def main():
    print("KV Cache 大小随上下文长度增长")
    print("=" * 50)
    print()
    print("以 Qwen2.5-7B 为例（28 层, 28 头, d_head=128, FP16=2bytes）：")
    print()
    print("公式：KV ≈ 2 × n_layers × n_heads × d_head × 2bytes × n_tokens")
    print()

    n_layers = 28
    n_heads = 28
    d_head = 128
    bytes_per_element = 2  # FP16

    kv_per_token = 2 * n_layers * n_heads * d_head * bytes_per_element
    kv_per_token_mb = kv_per_token / (1024 * 1024)

    print(f"每个 token 的 KV Cache：{kv_per_token:,} bytes = {kv_per_token_mb:.2f} MB")
    print()
    print(f"{'上下文长度':<15} {'KV Cache 大小':<20} {'累计显存估算':<20}")
    print("-" * 55)

    model_size_gb = 4.5  # Q4_K_M 约 4.5GB

    for ctx in [512, 1024, 2048, 4096, 8192, 16384, 32768]:
        kv_gb = (kv_per_token * ctx) / (1024 ** 3)
        total_gb = model_size_gb + kv_gb
        bar = "█" * int(kv_gb * 10)
        print(f"{ctx:<15} {kv_gb:>6.2f} GB {bar:<20} {total_gb:>6.2f} GB")

    print()
    print("观察：")
    print("  - 上下文翻倍 → KV Cache 翻倍（线性增长）")
    print("  - 7B Q4_K_M 在 8GB 显卡上：上下文最好不要超过 4096")
    print("  - 这就是为什么长上下文模型贵——显存消耗极快")
    print()
    print("显存估算对照：")
    print("  RTX 3060 (12GB)：够跑 4096 ctx，8192 可能不够")
    print("  RTX 4090 (24GB)：轻松跑 8192 ctx，16384 需要优化")
    print("  A100 (80GB)：    可以跑 32768+ ctx")


if __name__ == "__main__":
    main()
