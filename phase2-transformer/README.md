# Phase 2：模型如何"思考" — 手写 Transformer 前向传播

📌 **前置要求:** Phase 1（会用 API 调模型）

🎯 **学完你能回答:**
- Attention 机制的本质是什么？Q、K、V 分别做什么？
- 一个 token 从输入到输出经历了哪些步骤？
- 为什么 Transformer 能并行处理所有 token？
- 多头注意力（Multi-Head Attention）中每个"头"在做什么？

🗺️ **路线图:**
1. 跑 `transformer_annotated.py` — 看数据流的 shape 变化
2. 跑 `transformer.py` — 理解精简版的代码结构
3. 跑 `attention_viz.py` — 可视化 Attention 权重矩阵
4. 做 `exercises/` 里的练习

📖 **核心内容:**

### Token 的旅程

```
"我爱学习" → Tokenizer → [15, 234, 89, 2]
  → Embedding 查表 → 每个 ID 变 64 维向量
  → + 位置编码 → 告诉模型"这是第几个字"
  → N 个 Transformer 层 → 每层 = Attention + FFN
  → LM Head → 预测下一个 token
```

### Attention: 一切的核心

```
Q (查询): "我想找什么？"
K (键):   "我有什么？"
V (值):   "我的实际内容"

Attention = softmax(Q·K^T / √d_k) · V

直觉：你在人群中找"谁懂 C++"
  Q = 你的需求 "找懂 C++ 的人"
  K = 每个人身上的标签
  V = 每个人能提供的实际帮助
  Attention = 找到标签最匹配的人，获取他的帮助
```

> 🧠 后端视角：Attention ≈ 数据库查询优化器的"索引查找"——Q 是查询条件，
> K 是索引键，V 是行数据。softmax(Q·K^T) 是"这个索引键和查询条件的匹配度"。

### 为什么 Transformer 能并行

RNN 必须按顺序处理：读完"我"→ 读"爱"→ 读"学"。
Transformer 一次性看全部 token，Attention 让每个位置直接"沟通"。
这就是它能训练得这么快、这么大的原因。

🏃 **动手环节:**

```powershell
pip install numpy
python transformer_annotated.py   # 教学版：看每一步的 shape
python transformer.py             # 精简版：看整体结构
python attention_viz.py           # 可视化 Attention 矩阵
```

### 实验：改参数看变化

1. 把 `n_heads` 从 4 改成 8，观察 shape 变化
2. 把 `n_layers` 从 2 改成 4，思考为什么输出 shape 不变
3. 把 `seq_len` 从 6 改成 10，观察 Attention 矩阵变大

✅ **验收题:**
- [ ] 能画出 Attention(Q, K, V) 的数据流图
- [ ] 能解释 Q、K、V 各自的角色
- [ ] 能运行 transformer_annotated.py 并说出每一步在做什么
- [ ] 知道"残差连接"解决了什么问题

🔗 **下一步:** Phase 3 — 本地部署：在你自己电脑上跑真正的模型
