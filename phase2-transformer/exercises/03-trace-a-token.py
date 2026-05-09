"""
练习 3：跟踪一个 token 的数据流

在 transformer_annotated.py 的输出中，找到 token ID=234 ("喜欢")
在每一层的 shape 变化，画出它的旅程。
"""

print("""
Token "喜欢" (ID=234) 的旅程：

  [输入]
  token_id = 234                                ← 一个整数
      │
  [Embedding]
  embedding[234] → shape=(64,)                   ← 稠密向量
      │
  [+ 位置编码]
  pe[1]         → shape=(64,)                   ← 加上"第2个位置"
  x[0, 1, :]    → shape=(64,)                   ← 输入序列的第2个token的表示
      │
  [Layer 1: LayerNorm → Multi-Head Attention]
  Q[0, :, 1, :] → shape=(n_heads, d_k)          ← 4个头各自的查询向量
  和所有 K 算相似度 → attention[0, :, 1, :]     ← 对每个位置的关注度
  加权取 V        → attn_out[0, 1, :]            ← shape=(64,)
  x[0, 1, :] + attn_out[0, 1, :]                ← 残差连接
      │
  [Layer 1: LayerNorm → FFN]
  ffn_out[0, 1, :] → shape=(64,)
  x[0, 1, :] + ffn_out[0, 1, :]                 ← 残差连接
      │
  [Layer 2: 同上流程]
      │
  [LM Head]
  logits[0, 1, :] → shape=(1000,)               ← 第2个位置对词汇表的预测
  argmax → 预测下一个 token ID

  真正生成时，我们只关心最后一个位置的预测。
  最后一个位置预测的下一个 token → 拼到序列末尾 → 再来一轮。
  这就是"逐字生成"。
""")
