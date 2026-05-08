"""
minimal_transformer.py — Phase 6：手写 Transformer 前向传播

目标：用纯 numpy 实现 Transformer 的一次前向传播，理解 Attention 到底在算什么。

这是整个学习路径的"终极去黑盒"——你调了一年 API，现在看看里面到底发生了什么。

不包含训练（反向传播），只有推理（前向传播）。训练是另一套复杂度。

依赖：numpy
用法：
    pip install numpy
    python minimal_transformer.py

输出：
    每一步的数据形状和中间结果，让你跟踪数据流。

参考：
    - The Illustrated Transformer (jalammar.github.io)
    - 3Blue1Brown 注意力机制视频
    - "Attention Is All You Need" 论文（最后再看）
"""

import numpy as np


# =========================================================================
# 1. 输入：把文字变成数字
# =========================================================================

def token_embedding(token_ids: np.ndarray, embedding_matrix: np.ndarray) -> np.ndarray:
    """
    查表：把每个 token ID 映射成一个稠密向量。

    输入：token_ids      → (seq_len,)          例如 [15, 234, 89, 2]
          embedding_matrix → (vocab_size, d_model)  词汇表 × 向量维度
    输出：               → (seq_len, d_model)   每个 token 变成了一个向量

    直觉：每个词在"语义空间"里有一个坐标。"猫"和"狗"的坐标很近，"猫"和"汽车"很远。
    """
    return embedding_matrix[token_ids]


# =========================================================================
# 2. 位置编码：让模型知道"顺序"
# =========================================================================

def sinusoidal_positional_encoding(seq_len: int, d_model: int) -> np.ndarray:
    """
    Transformer 没有"顺序"的概念——它同时看所有 token。
    所以需要手动注入位置信息。这里用正弦/余弦编码。

    输出：(seq_len, d_model)
    """
    pos = np.arange(seq_len)[:, np.newaxis]       # (seq_len, 1)
    i = np.arange(d_model)[np.newaxis, :]          # (1, d_model)

    angle = pos / np.power(10000, (2 * (i // 2)) / d_model)

    pe = np.zeros((seq_len, d_model))
    pe[:, 0::2] = np.sin(angle[:, 0::2])  # 偶数维度用 sin
    pe[:, 1::2] = np.cos(angle[:, 1::2])  # 奇数维度用 cos

    return pe


# =========================================================================
# 3. 自注意力（Self-Attention）：整篇的核心
# =========================================================================

def scaled_dot_product_attention(
    Q: np.ndarray, K: np.ndarray, V: np.ndarray,
    mask: np.ndarray | None = None,
) -> np.ndarray:
    """
    Attention 的计算过程：

    步骤：
      1. Q × K^T → 计算"谁跟谁相关"（注意力分数）
      2. ÷ sqrt(d_k) → 缩放，防止分数太大导致 softmax 饱和
      3. softmax → 把分数变成概率（总和=1）
      4. × V → 按概率加权取 Value

    直觉：
      你在一屋子人里找"谁懂 C++"。
      Q = 你的问题"谁懂 C++？"
      K = 每个人身上的标签"我懂 Python / 我懂 C++ / 我懂 Rust"
      V = 每个人能提供的实际帮助
      Attention = 找到标签最匹配的人(K)，获取他的帮助(V)

    输入：
      Q, K, V → (batch, n_heads, seq_len, d_k)
    输出：
      → (batch, n_heads, seq_len, d_k)
    """
    d_k = Q.shape[-1]

    # Step 1: 计算注意力分数（点积）
    scores = Q @ K.transpose(0, 1, 3, 2)  # (..., seq_len, seq_len)

    # Step 2: 缩放
    scores = scores / np.sqrt(d_k)

    # Step 3: Mask（可选）—— 让模型看不到"未来"的 token
    if mask is not None:
        scores = scores + mask

    # Step 4: Softmax
    scores = scores - scores.max(axis=-1, keepdims=True)  # 数值稳定
    exp_scores = np.exp(scores)
    attention_weights = exp_scores / exp_scores.sum(axis=-1, keepdims=True)

    # Step 5: 加权求和
    output = attention_weights @ V

    return output


def multi_head_attention(
    x: np.ndarray,
    W_Q: np.ndarray, W_K: np.ndarray, W_V: np.ndarray, W_O: np.ndarray,
    n_heads: int,
    mask: np.ndarray | None = None,
) -> np.ndarray:
    """
    多头注意力 = 把 Q/K/V 切成 n_heads 份，每份独立做 Attention，最后拼回来。

    为什么要多头？一个头可能关注"语法结构"，另一个头关注"语义含义"，
    再一个头关注"指代关系"。多个头能捕捉不同类型的关系。

    输入：
      x → (batch, seq_len, d_model)
      W_Q, W_K, W_V → (d_model, d_model)  投影矩阵
      W_O → (d_model, d_model)            输出投影
    输出：
      → (batch, seq_len, d_model)
    """
    batch, seq_len, d_model = x.shape
    d_k = d_model // n_heads

    # 线性投影
    Q = x @ W_Q  # (batch, seq_len, d_model)
    K = x @ W_K
    V = x @ W_V

    # 切分成多头
    Q = Q.reshape(batch, seq_len, n_heads, d_k).transpose(0, 2, 1, 3)
    K = K.reshape(batch, seq_len, n_heads, d_k).transpose(0, 2, 1, 3)
    V = V.reshape(batch, seq_len, n_heads, d_k).transpose(0, 2, 1, 3)

    # 对每个头做 Attention
    attn_output = scaled_dot_product_attention(Q, K, V, mask)

    # 拼回头
    attn_output = attn_output.transpose(0, 2, 1, 3).reshape(batch, seq_len, d_model)

    # 最终投影
    return attn_output @ W_O


# =========================================================================
# 4. 前馈网络（Feed-Forward Network）
# =========================================================================

def feed_forward(x: np.ndarray, W1: np.ndarray, W2: np.ndarray) -> np.ndarray:
    """
    对每个 token 独立做两次线性变换 + 一次激活。

    输入：x  → (batch, seq_len, d_model)
          W1 → (d_model, d_ff)  通常是 d_model 的 4 倍
          W2 → (d_ff, d_model)
    输出：→ (batch, seq_len, d_model)

    直觉：Attention 负责"token 之间交流"，FFN 负责"每个 token 独立思考"。
    """
    hidden = x @ W1                # 升维
    hidden = np.maximum(0, hidden)  # ReLU 激活
    return hidden @ W2              # 降维回来


# =========================================================================
# 5. 层归一化（Layer Normalization）
# =========================================================================

def layer_norm(x: np.ndarray, gamma: np.ndarray, beta: np.ndarray, eps: float = 1e-6) -> np.ndarray:
    """
    把每个 token 的向量归一化到均值 0、标准差 1，然后缩放和平移。

    作用：让深层网络能稳定训练。没有它，数值会爆炸或消失。
    """
    mean = x.mean(axis=-1, keepdims=True)
    var = x.var(axis=-1, keepdims=True)
    return gamma * (x - mean) / np.sqrt(var + eps) + beta


# =========================================================================
# 6. 拼起来：一个完整的 Transformer 层
# =========================================================================

def transformer_layer(
    x: np.ndarray,
    attn_params: dict,
    ffn_params: dict,
    ln_params: dict,
    n_heads: int,
    mask: np.ndarray | None = None,
) -> np.ndarray:
    """
    一个 Transformer 层 = Attention + FFN，每步都有残差连接和层归一化。

    流程：
      x → LN → Attention → + x (残差) → LN → FFN → + x (残差) → 输出

    残差连接（+ x）：把输入直接加到输出上。如果 Attention/FFN 学到了"什么都不做"，
    至少输入还能原样传过去。这是深层网络能训练的关键。
    """
    # 子层 1：Multi-Head Attention + 残差
    attn_in = layer_norm(x, **ln_params["attn_ln"])
    attn_out = multi_head_attention(attn_in, **attn_params, n_heads=n_heads, mask=mask)
    x = x + attn_out  # 残差连接

    # 子层 2：Feed-Forward + 残差
    ffn_in = layer_norm(x, **ln_params["ffn_ln"])
    ffn_out = feed_forward(ffn_in, **ffn_params)
    x = x + ffn_out  # 残差连接

    return x


# =========================================================================
# 7. 完整模型：Token → Embedding → Layers → Output
# =========================================================================

def transformer_forward(
    token_ids: np.ndarray,
    embedding: np.ndarray,
    positional_encoding: np.ndarray,
    layers: list[dict],
    lm_head: np.ndarray,
    n_heads: int,
    mask: np.ndarray | None = None,
) -> np.ndarray:
    """
    Transformer 的完整前向传播。

    流程：
      token_ids → embedding 查表 → + 位置编码
      → Layer 1 → Layer 2 → ... → Layer N
      → lm_head 投影 → logits（每个位置预测下一个 token 的概率）

    输入：
      token_ids → (batch, seq_len)  例如 [[15, 234, 89, 2]]
    输出：
      logits    → (batch, seq_len, vocab_size)  每个位置对词汇表的"倾向"
    """
    # Embedding
    x = token_embedding(token_ids, embedding)

    # + 位置编码
    x = x + positional_encoding[:token_ids.shape[1], :]

    # 通过每一层
    for layer in layers:
        x = transformer_layer(x, **layer, n_heads=n_heads, mask=mask)

    # 最终投影到词汇表大小
    logits = x @ lm_head.T

    return logits


# =========================================================================
# Demo：用随机权重跑一遍，观察数据流
# =========================================================================

def demo():
    print("=" * 65)
    print("  迷你 Transformer — 一次完整的前向传播")
    print("  目标：看清每一步数据的形状变化")
    print("=" * 65)

    # 超参数（模拟一个小模型）
    vocab_size = 1000       # 词汇表大小
    d_model = 64            # 向量维度（GPT-3 是 12288）
    n_heads = 4             # 注意力头数
    d_ff = 256              # FFN 隐藏层维度（通常是 d_model 的 4 倍）
    n_layers = 2            # Transformer 层数
    seq_len = 6             # 输入序列长度

    np.random.seed(42)

    # 模拟输入："我 喜欢 学习 大模型 [EOS]"
    token_ids = np.array([[15, 234, 89, 567, 2, 0]])  # (1, seq_len)

    # --- 1. Embedding ---
    embedding = np.random.randn(vocab_size, d_model).astype(np.float32)
    x = token_embedding(token_ids, embedding)
    print(f"\n1. Embedding 之后：{x.shape}  ← (batch=1, seq_len={seq_len}, d_model={d_model})")

    # --- 2. 位置编码 ---
    pe = sinusoidal_positional_encoding(seq_len, d_model)
    x = x + pe[:seq_len, :]
    print(f"2. + 位置编码：    {x.shape}  <- 每个位置有了'第几个字'的信息")

    # --- 3. 因果 Mask（让模型看不到未来） ---
    # 在生成任务中，第 i 个位置只能看到 0~i 的 token
    causal_mask = np.triu(np.ones((seq_len, seq_len)) * -1e9, k=1)
    print(f"3. 因果 Mask：    让每个位置只看到它之前的 token（不能偷看未来）")

    # --- 4. 构建 Transformer 层 ---
    d_k = d_model // n_heads
    layers = []
    for i in range(n_layers):
        layer = {
            "attn_params": {
                "W_Q": np.random.randn(d_model, d_model).astype(np.float32) * 0.02,
                "W_K": np.random.randn(d_model, d_model).astype(np.float32) * 0.02,
                "W_V": np.random.randn(d_model, d_model).astype(np.float32) * 0.02,
                "W_O": np.random.randn(d_model, d_model).astype(np.float32) * 0.02,
            },
            "ffn_params": {
                "W1": np.random.randn(d_model, d_ff).astype(np.float32) * 0.02,
                "W2": np.random.randn(d_ff, d_model).astype(np.float32) * 0.02,
            },
            "ln_params": {
                "attn_ln": {"gamma": np.ones(d_model), "beta": np.zeros(d_model)},
                "ffn_ln":  {"gamma": np.ones(d_model), "beta": np.zeros(d_model)},
            },
        }
        layers.append(layer)

    # --- 5. LM Head（最后一层投影） ---
    lm_head = np.random.randn(vocab_size, d_model).astype(np.float32) * 0.02

    # --- 6. 前向传播！ ---
    print(f"\n4. 通过 {n_layers} 个 Transformer 层...")
    logits = transformer_forward(
        token_ids, embedding, pe, layers, lm_head, n_heads, causal_mask,
    )
    print(f"   输出 logits：{logits.shape}  ← (batch=1, seq_len={seq_len}, vocab_size={vocab_size})")

    # --- 7. 取最后一个位置的预测 ---
    last_logits = logits[0, -1, :]   # 最后一个 token 位置的预测
    predicted_token = int(np.argmax(last_logits))
    print(f"\n5. 最后一个位置预测的下一个 token：{predicted_token}")
    print(f"   （因为权重是随机的，所以预测结果也是随机的——这是正常的）")

    # --- 总结 ---
    print("\n" + "=" * 65)
    print("  关键观察")
    print("=" * 65)
    print(f"""
  每个 token 进来是一个 ID（整数）
    → Embedding 变成 {d_model} 维向量
    → + 位置编码（告诉模型顺序）
    → 通过 {n_layers} 个 Transformer 层：
       每层 = Attention（token 之间交流）+ FFN（每个 token 独立思考）
    → 最后投影到 {vocab_size} 维（每个词一个分数）
    → 选分数最高的那个词 → 这就是模型"生成"的下一个 token

  你刚才看到的，就是每次 API 调用时服务器在做的事。
  只不过真正的模型 {d_model} 更大（1024-12288），层更多（12-96），
  循环更久（一直生成到 [EOS] 或达到 max_tokens）。
  """)

    # --- 额外：展示 Attention 权重 ---
    print("=" * 65)
    print("  附加：看看 Attention 权重长什么样")
    print("=" * 65)
    print("（取 Layer 1 的 Attention，第一个头，最后一个 token）")

    x_demo = token_embedding(token_ids, embedding) + pe[:seq_len, :]
    Q = x_demo @ layers[0]["attn_params"]["W_Q"]
    K = x_demo @ layers[0]["attn_params"]["W_K"]
    Q = Q.reshape(1, seq_len, n_heads, d_k).transpose(0, 2, 1, 3)
    K = K.reshape(1, seq_len, n_heads, d_k).transpose(0, 2, 1, 3)
    scores = Q @ K.transpose(0, 1, 3, 2) / np.sqrt(d_k)
    scores = scores + causal_mask
    scores = scores - scores.max(axis=-1, keepdims=True)
    weights = np.exp(scores) / np.exp(scores).sum(axis=-1, keepdims=True)

    print(f"\n  输入 token：我(15) 喜欢(234) 学习(89) 大模型(567) [EOS](2) [PAD](0)")
    print(f"  最后一个 token([PAD]) 对各位置的注意力分布：")
    attn = weights[0, 0, -1, :]  # batch=0, head=0, last position

    token_labels = ["我(15)", "喜欢(234)", "学习(89)", "大模型(567)", "[EOS](2)", "[PAD](0)"]
    for label, w in zip(token_labels, attn):
        bar = "#" * int(w * 50)
        print(f"    {label:12s}  {w:.3f}  {bar}")


if __name__ == "__main__":
    demo()
