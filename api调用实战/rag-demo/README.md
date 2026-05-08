# RAG Demo — 检索增强生成

> Phase 3：让模型基于你的私有数据回答问题

## 一句话理解

RAG = 先搜后问。

模型不知道你的私有数据。RAG 在做的事：**把你的文档切成块 → 向量化存起来 → 每次提问先搜相关块 → 拼进 prompt 里发给模型**。

## 架构

```
用户提问 "什么是 KV Cache？"
  │
  ├─→ 向量化（sentence-transformers）
  │     └─→ 向量检索（余弦相似度）
  │           └─→ 找到最相关的 3 个文档块
  │
  └─→ 把文档块拼进 Prompt：
        "基于以下文档：<文档块1><文档块2><文档块3>
         回答问题：什么是 KV Cache？"
        │
        └─→ LLM 回答（基于你的文档）
```

## 安装

```powershell
# 安装依赖（首次运行会自动下载约 400MB 的 embedding 模型）
cd api调用实战/rag-demo
pip install -r requirements.txt
```

## 运行

```powershell
# 交互模式
$env:DEEPSEEK_API_KEY="sk-..."
python rag.py

# 单次查询
python rag.py --query "什么是 KV Cache？"

# 对比模式（看看不加 RAG 模型能答对吗？）
python rag.py --query "怎么设置环境变量？" --compare

# 看详细过程
python rag.py --query "Proxy 测试脚本有哪些？" --verbose
```

## 试试这些查询

RAG 加了关于本项目的文档，模型原本不知道这些信息：

| 查询 | 说明 |
|------|------|
| `"CLI 聊天客户端支持哪些功能？"` | 模型应基于你的文档回答 |
| `"如何设置环境变量？"` | 模型应列出三个环境变量名 |
| `"什么是 KV Cache？"` | 模型应给出工程化解释 |
| `"Proxy 测试脚本有哪些？"` | 模型应说出 test_chat 和 test_stream |

## 对比实验

```powershell
# 不加 RAG 直接问
python rag.py --query "本项目有哪些环境变量？" --compare
```

预期结果：
- **不加 RAG**：模型说不知道，或者给出通用答案
- **加 RAG**：模型准确列出 DEEPSEEK_API_KEY、OPENAI_API_KEY、PROXY_API_KEY

## 内部原理

```
rag.py 做了什么：

1. load_sample_document()
   └─ 加载内置文档（描述本项目）

2. chunk_text()
   └─ 把长文档切成 300 词一块，50 词重叠
   └─ 重叠保证块之间的上下文连贯

3. SimpleVectorStore.add_documents()
   └─ sentence-transformers 把每个块转成 384 维向量
   └─ 向量存内存里

4. search(query)
   └─ 查询也转成 384 维向量
   └─ 余弦相似度找最接近的 top-3

5. ask_llm(query, context_chunks)
   └─ 把文档块拼成："基于以下文档：... 回答问题：..."
   └─ 发给 LLM 生成最终答案
```

## 生产环境替代

| 组件 | 本 demo 用 | 生产用 |
|------|-----------|--------|
| Embedding | sentence-transformers | OpenAI Embeddings / bge |
| 向量存储 | numpy 内存数组 | chromadb / qdrant / pgvector |
| 分块 | 固定字符数 | 智能分块（按段落/语义） |
| 检索 | 余弦相似度 | 混合检索（向量 + BM25） |
| LLM | DeepSeek API | 同左或本地模型 |
