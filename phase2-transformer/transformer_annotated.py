"""
transformer_annotated.py — Phase 2 教学版：手写 Transformer 前向传播

和 transformer.py 功能完全一样，但每一步打印输入输出的 shape 和含义。
适合第一次运行——跟着 shape 的变化理解数据流。
跑通后再去看 transformer.py 的精简版。

用法：
    pip install numpy
    python transformer_annotated.py
"""

import numpy as np


def section(title: str):
    """打印章节标题"""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}")


def show(name: str, arr: np.ndarray):
    """打印数组的名称和形状"""
    print(f"  {name:30s}  shape={str(arr.shape):20s}  dtype={arr.dtype}")


def explain(text: str):
    """打印解释文字"""
    print(f"    => {text}")


# =========================================================================
# 1. Embedding：把 token ID 变成向量
# =========================================================================

def token_embedding(token_ids: np.ndarray, embedding_matrix: np.ndarray) -> np.ndarray:
    result = embedding_matrix[token_ids]
    show("token_ids", token_ids)
    show("embedding_matrix (词汇表)", embedding_matrix)
    show("→ 查表结果", result)
    explain(f"每个 token ID 在 embedding_matrix 里找到对应的行")
    explain(f"一个整数 → 一个 {result.shape[-1]} 维的稠密向量")
    return result


# =========================================================================
# 2. 位置编码：注入顺序信息
# =========================================================================

def sinusoidal_positional_encoding(seq_len: int, d_model: int) -> np.ndarray:
    pos = np.arange(seq_len)[:, np.newaxis]
    i = np.arange(d_model)[np.newaxis, :]
    angle = pos / np.power(10000, (2 * (i // 2)) / d_model)

    pe = np.zeros((seq_len, d_model))
    pe[:, 0::2] = np.sin(angle[:, 0::2])
    pe[:, 1::2] = np.cos(angle[:, 1::2])

    show("位置编码矩阵", pe)
    explain(f"({seq_len}, {d_model}) — 每行是一个位置的'指纹'")
    explain("偶数列用 sin，奇数列用 cos——这是论文里的标准做法")
    return pe


# =========================================================================
# 3. 自注意力：核心机制
# =========================================================================

def scaled_dot_product_attention(
    Q: np.ndarray, K: np.ndarray, V: np.ndarray,
    mask: np.ndarray | None = None,
) -> np.ndarray:
    d_k = Q.shape[-1]
    show("Q (查询)", Q)
    show("K (键)", K)
    show("V (值)", V)
    explain("Q=我要找什么, K=每个位置有什么, V=每个位置的实际内容")

    # Step 1: 计算分数
    scores = Q @ K.transpose(0, 1, 3, 2)
    show("Q @ K^T (注意力分数)", scores)
    explain(f"形状 ({scores.shape[-2]}, {scores.shape[-1]}) — 每个 token 对每个 token 的相关性")

    # Step 2: 缩放
    scores = scores / np.sqrt(d_k)
    explain(f"÷ sqrt(d_k={d_k}) = ÷ {np.sqrt(d_k):.1f}  — 防止点积太大，softmax 饱和")

    # Step 3: Mask
    if mask is not None:
        scores = scores + mask
        explain("加上因果 mask：让位置 i 只能看到 0~i")

    # Step 4: Softmax
    scores = scores - scores.max(axis=-1, keepdims=True)
    exp_scores = np.exp(scores)
    attention_weights = exp_scores / exp_scores.sum(axis=-1, keepdims=True)
    show("Softmax 后 (注意力权重)", attention_weights)
    explain("每行的和 = 1.0 — 像一个概率分布")

    # Step 5: 加权求和
    output = attention_weights @ V
    show("注意力输出 (权重×V)", output)
    explain("用注意力权重对 V 做加权平均——关注度越高，贡献越大")

    return output


def multi_head_attention(
    x: np.ndarray,
    W_Q: np.ndarray, W_K: np.ndarray, W_V: np.ndarray, W_O: np.ndarray,
    n_heads: int,
    mask: np.ndarray | None = None,
) -> np.ndarray:
    batch, seq_len, d_model = x.shape
    d_k = d_model // n_heads

    show("多头注意力输入 x", x)

    Q = x @ W_Q
    K = x @ W_K
    V = x @ W_V
    show("  投影后 Q", Q)
    show("  投影后 K", K)
    show("  投影后 V", V)
    explain(f"线性投影：把 d_model={d_model} 映射为 Q/K/V 空间")

    Q = Q.reshape(batch, seq_len, n_heads, d_k).transpose(0, 2, 1, 3)
    K = K.reshape(batch, seq_len, n_heads, d_k).transpose(0, 2, 1, 3)
    V = V.reshape(batch, seq_len, n_heads, d_k).transpose(0, 2, 1, 3)
    show("  切分后 Q (多头)", Q)
    explain(f"切成 {n_heads} 个头，每个头维度 d_k={d_k}")
    explain("每个头独立做 Attention，关注不同类型的关系")

    print(f"\n  --- 对 {n_heads} 个头分别做 Attention ---")
    attn_output = scaled_dot_product_attention(Q, K, V, mask)

    attn_output = attn_output.transpose(0, 2, 1, 3).reshape(batch, seq_len, d_model)
    show("  拼回头", attn_output)
    explain(f"把 {n_heads} 个头拼回 d_model={d_model} 维")

    output = attn_output @ W_O
    show("  输出投影后", output)
    explain("W_O 把多头信息融合成一个统一的表示")

    return output


# =========================================================================
# 4. 前馈网络
# =========================================================================

def feed_forward(x: np.ndarray, W1: np.ndarray, W2: np.ndarray) -> np.ndarray:
    show("FFN 输入", x)
    hidden = x @ W1
    show("  W1 升维后", hidden)
    explain(f"d_model → d_ff ({W1.shape[-1]})，通常升 4 倍——给足够的容量")

    hidden = np.maximum(0, hidden)
    explain("ReLU 激活：max(0, x)——引入非线性")

    output = hidden @ W2
    show("  W2 降维后 (FFN 输出)", output)
    explain(f"d_ff → d_model，恢复原始维度")

    return output


# =========================================================================
# 5. 层归一化
# =========================================================================

def layer_norm(x: np.ndarray, gamma: np.ndarray, beta: np.ndarray, eps: float = 1e-6) -> np.ndarray:
    mean = x.mean(axis=-1, keepdims=True)
    var = x.var(axis=-1, keepdims=True)
    show("LN 输入", x)
    normed = (x - mean) / np.sqrt(var + eps)
    result = gamma * normed + beta
    show("LN 输出", result)
    explain(f"均值={mean[0,0,0]:.3f}, 方差={var[0,0,0]:.3f}  → 归一化到均值0方差1")
    return result


# =========================================================================
# 6. Transformer 层
# =========================================================================

def transformer_layer(
    x: np.ndarray,
    attn_params: dict,
    ffn_params: dict,
    ln_params: dict,
    n_heads: int,
    layer_idx: int,
    mask: np.ndarray | None = None,
) -> np.ndarray:
    print(f"\n  {'─' * 60}")
    print(f"  Layer {layer_idx + 1}")
    print(f"  {'─' * 60}")

    # 子层 1: Attention + 残差
    attn_in = layer_norm(x, **ln_params["attn_ln"])
    attn_out = multi_head_attention(attn_in, **attn_params, n_heads=n_heads, mask=mask)
    x = x + attn_out
    show("Attention + 残差后", x)
    explain("残差连接：x + Attention(x)——即使 Attention 学到的是 0，输入也能原样传过去")

    # 子层 2: FFN + 残差
    ffn_in = layer_norm(x, **ln_params["ffn_ln"])
    ffn_out = feed_forward(ffn_in, **ffn_params)
    x = x + ffn_out
    show("FFN + 残差后", x)
    explain("残差连接：x + FFN(x)")

    return x


# =========================================================================
# 7. 完整前向传播
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
    section("Step 1: Embedding 查表")
    x = token_embedding(token_ids, embedding)

    section("Step 2: 加位置编码")
    x = x + positional_encoding[:token_ids.shape[1], :]
    show("Embedding + 位置编码", x)
    explain("位置编码和 embedding 直接相加——简单的做法，但效果很好")

    section("Step 3: 通过 Transformer 层")
    for i, layer in enumerate(layers):
        x = transformer_layer(x, **layer, n_heads=n_heads, layer_idx=i, mask=mask)

    section("Step 4: 最终投影 (LM Head)")
    logits = x @ lm_head.T
    show("输出 logits", logits)
    explain(f"({logits.shape[-2]} 个位置) × ({logits.shape[-1]} 个候选词)")
    explain("每个位置对词汇表中每个词的'倾向'——分数越高越可能是下一个 token")

    return logits


# =========================================================================
# Demo
# =========================================================================

def demo():
    print("=" * 70)
    print("  迷你 Transformer — 带 shape 注解的完整前向传播")
    print("  零数学，只看数据形状变化")
    print("=" * 70)

    vocab_size = 1000
    d_model = 64
    n_heads = 4
    d_ff = 256
    n_layers = 2
    seq_len = 6

    np.random.seed(42)

    token_ids = np.array([[15, 234, 89, 567, 2, 0]])

    section("超参数")
    print(f"  vocab_size={vocab_size}  (词汇表大小)")
    print(f"  d_model={d_model}        (向量维度，GPT-3 是 12288)")
    print(f"  n_heads={n_heads}         (注意力头数)")
    print(f"  d_ff={d_ff}          (FFN 隐藏层维度 = d_model×4)")
    print(f"  n_layers={n_layers}        (Transformer 层数)")
    print(f"  seq_len={seq_len}         (输入序列长度)")
    print(f"  输入 token IDs: {token_ids[0].tolist()}")

    embedding = np.random.randn(vocab_size, d_model).astype(np.float32)
    pe = sinusoidal_positional_encoding(seq_len, d_model)
    causal_mask = np.triu(np.ones((seq_len, seq_len)) * -1e9, k=1)

    d_k = d_model // n_heads
    layers = []
    for i in range(n_layers):
        layers.append({
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
                "ffn_ln": {"gamma": np.ones(d_model), "beta": np.zeros(d_model)},
            },
        })

    lm_head = np.random.randn(vocab_size, d_model).astype(np.float32) * 0.02

    logits = transformer_forward(
        token_ids, embedding, pe, layers, lm_head, n_heads, causal_mask,
    )

    last_logits = logits[0, -1, :]
    predicted_token = int(np.argmax(last_logits))

    section("总结")
    print(f"""
  一条 token ID 的数据旅程：

  整数 [{', '.join(str(t) for t in token_ids[0])}]
    → Embedding 查表：每个 ID 变成 {d_model} 维向量
    → + 位置编码：注入"第几个位置"的信息
    → 通过 {n_layers} 个 Transformer 层：
        每层 = LayerNorm → 多头 Attention → + 残差
             → LayerNorm → FFN (升维→ReLU→降维) → + 残差
    → LM Head 投影到 {vocab_size} 维
    → argmax 取最大值 → 预测下一个 token = {predicted_token}

  真正的 GPT 模型只是把数字放大：
    d_model=768~12288, n_layers=12~96, vocab_size=50000~100000
  核心计算完全一样。
  """)

    # 展示 Attention 权重
    section("附加：看看 Attention 权重矩阵")
    print("  输入 token: 我(15) 喜欢(234) 学习(89) 大模型(567) [EOS](2) [PAD](0)")
    print()

    x_demo = token_embedding(token_ids, embedding) + pe[:seq_len, :]
    Q_d = x_demo @ layers[0]["attn_params"]["W_Q"]
    K_d = x_demo @ layers[0]["attn_params"]["W_K"]
    Q_d = Q_d.reshape(1, seq_len, n_heads, d_k).transpose(0, 2, 1, 3)
    K_d = K_d.reshape(1, seq_len, n_heads, d_k).transpose(0, 2, 1, 3)
    scores_d = Q_d @ K_d.transpose(0, 1, 3, 2) / np.sqrt(d_k)
    scores_d = scores_d + causal_mask
    scores_d = scores_d - scores_d.max(axis=-1, keepdims=True)
    weights_d = np.exp(scores_d) / np.exp(scores_d).sum(axis=-1, keepdims=True)

    token_labels = ["我(15)", "喜欢(234)", "学习(89)", "大模型(567)", "[EOS](2)", "[PAD](0)"]

    for h in range(min(n_heads, 2)):
        print(f"  Head {h + 1} 的注意力矩阵（行=查询者, 列=被关注者, 因果mask导致上三角为0）：")
        print(f"    {'':12s}", end="")
        for label in token_labels:
            print(f"{label:>10s}", end="")
        print()
        for i, from_label in enumerate(token_labels):
            print(f"    {from_label:12s}", end="")
            for j in range(seq_len):
                w = weights_d[0, h, i, j]
                if w > 0.01:
                    print(f"{w:10.3f}", end="")
                else:
                    print(f"{'0':>10s}", end="")
            print()
        print()

    print("  观察：")
    print("  - 每行的和 = 1.0（概率分布）")
    print("  - 上三角全是 0（因果mask——不能让当前位置看到未来）")
    print("  - 每个头可能关注不同的模式")
    print("  - 因为权重是随机的，这里的分布没有实际意义——真正的模型训练后会学到有意义的模式")


if __name__ == "__main__":
    demo()
