"""
练习 1：手算一个 Attention 矩阵

给定简化的 Q、K、V 值，手动计算 Attention 的输出。
跑完脚本后对比你的手算结果和程序输出。

提示：用纸笔一步步算。
  1. Q @ K^T
  2. ÷ sqrt(d_k)
  3. softmax (每行)
  4. @ V
"""

import numpy as np

# 简化设置：d_k=2, seq_len=3
Q = np.array([[[[1.0, 0.0],
                [0.0, 1.0],
                [1.0, 1.0]]]])  # (1, 1, 3, 2)

K = np.array([[[[1.0, 0.0],
                [0.0, 1.0],
                [1.0, 1.0]]]])  # (1, 1, 3, 2)

V = np.array([[[[1.0, 2.0],
                [3.0, 4.0],
                [5.0, 6.0]]]])  # (1, 1, 3, 2)

d_k = 2

print("Q =")
print(Q[0, 0])
print("\nK =")
print(K[0, 0])
print("\nV =")
print(V[0, 0])

print("\n" + "=" * 40)
print("第 1 步：Q @ K^T (注意力分数)")
scores = Q @ K.transpose(0, 1, 3, 2)
print(scores[0, 0])

print("\n第 2 步：÷ sqrt(d_k) = ÷", np.sqrt(d_k))
scores = scores / np.sqrt(d_k)
print(scores[0, 0])

print("\n第 3 步：Softmax (每行)")
scores = scores - scores.max(axis=-1, keepdims=True)
exp_scores = np.exp(scores)
attn_weights = exp_scores / exp_scores.sum(axis=-1, keepdims=True)
print(attn_weights[0, 0])
print("(验证：每行和应该 = 1)")
print("行和：", attn_weights[0, 0].sum(axis=-1))

print("\n第 4 步：加权求和 (× V)")
output = attn_weights @ V
print(output[0, 0])

print("\n[OK] 对比你的手算结果，是否一致？")
print("  如果一致 → 你理解了 Attention 的计算过程")
print("  如果不一致 → 检查每一步，特别是在 softmax 之前有没有减去最大值")
