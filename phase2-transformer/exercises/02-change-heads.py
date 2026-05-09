"""
练习 2：修改 n_heads，观察 shape 变化

运行 transformer_annotated.py，分别设 n_heads=2, 4, 8。
观察：d_k 怎么变？每个头的"视野"怎么变？
"""

import numpy as np

d_model = 64

for n_heads in [2, 4, 8]:
    d_k = d_model // n_heads
    print(f"n_heads={n_heads:2d}  →  d_k={d_k:2d}  "
          f"→ 每个头处理 {d_k}/{d_model} = {d_k/d_model:.0%} 的维度")
    print(f"         每个头的 Attention 矩阵: (seq_len, seq_len) 不变")
    print(f"         每个头的 Q/K/V 形状: (batch, seq_len, {d_k})")
    print()

print("思考题：")
print("1. 头数越多越好吗？为什么？")
print("2. d_k 太小会有什么问题？")
print("3. GPT-3 的 d_model=12288, n_heads=96, 每个 d_k=128。")
print("   为什么选这个组合？")
