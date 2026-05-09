"""Visualize attention weights from the transformer demo."""

import numpy as np
from transformer import (
    token_embedding,
    sinusoidal_positional_encoding,
)


def main():
    vocab_size = 1000
    d_model = 64
    n_heads = 4
    seq_len = 6
    d_k = d_model // n_heads

    np.random.seed(42)
    token_ids = np.array([[15, 234, 89, 567, 2, 0]])
    token_labels = ["我", "喜欢", "学习", "大模型", "[EOS]", "[PAD]"]

    embedding = np.random.randn(vocab_size, d_model).astype(np.float32)
    pe = sinusoidal_positional_encoding(seq_len, d_model)
    x = token_embedding(token_ids, embedding) + pe[:seq_len, :]

    W_Q = np.random.randn(d_model, d_model).astype(np.float32) * 0.02
    W_K = np.random.randn(d_model, d_model).astype(np.float32) * 0.02
    W_V = np.random.randn(d_model, d_model).astype(np.float32) * 0.02

    Q = x @ W_Q
    K = x @ W_K
    Q = Q.reshape(1, seq_len, n_heads, d_k).transpose(0, 2, 1, 3)
    K = K.reshape(1, seq_len, n_heads, d_k).transpose(0, 2, 1, 3)

    scores = Q @ K.transpose(0, 1, 3, 2) / np.sqrt(d_k)
    causal_mask = np.triu(np.ones((seq_len, seq_len)) * -1e9, k=1)
    scores = scores + causal_mask
    scores = scores - scores.max(axis=-1, keepdims=True)
    weights = np.exp(scores) / np.exp(scores).sum(axis=-1, keepdims=True)

    # ASCII heatmap
    print("Attention Weights Heatmap (Head 1)")
    print("Rows = query position, Cols = key position")
    print()
    print(f"{'':12s}", end="")
    for label in token_labels:
        print(f"{label:>8s}", end="")
    print()

    for i, label_i in enumerate(token_labels):
        print(f"{label_i:12s}", end="")
        for j in range(seq_len):
            w = weights[0, 0, i, j]
            blocks = min(int(w * 40), 40)
            bar = "█" * blocks
            print(f" {bar:<8s}", end="") if blocks > 0 else print(f" {'·':<8s}", end="")
        print()

    print()
    print("█ = higher attention    · = masked (can't see future)")

    # Statistics
    print(f"\nPer-head attention entropy (higher = more spread out):")
    for h in range(n_heads):
        entropy = -np.sum(weights[0, h] * np.log(weights[0, h] + 1e-9)) / seq_len
        print(f"  Head {h+1}: {entropy:.3f}")

    print("\nNote: These weights are from random initialization — no meaningful pattern yet.")
    print("In a trained model, you'd see patterns like:")
    print("  - Next-token positions paying attention to previous tokens")
    print("  - Syntactic heads attending to nearby words")
    print("  - Semantic heads attending to related concepts across the sentence")


if __name__ == "__main__":
    main()
