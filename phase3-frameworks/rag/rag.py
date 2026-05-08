"""
rag.py — 检索增强生成（RAG）完整实现

流程：
  用户提问
    → 1. 向量化（Embedding 模型）
    → 2. 向量数据库检索（相似度搜索）
    → 3. 把相关文档片段拼入 Prompt
    → 4. LLM 基于上下文回答

用法：
    pip install sentence-transformers numpy openai tomli
    python rag.py --query "你的问题"

示例：
    python rag.py --query "什么是 KV Cache？"
    python rag.py --query "如何设置环境变量？" --verbose
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
from sentence_transformers import SentenceTransformer

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


# =========================================================================
# 配置
# =========================================================================

DEFAULT_CONFIG = {
    "api_key": "$DEEPSEEK_API_KEY",
    "base_url": "https://api.deepseek.com",
    "model": "deepseek-chat",
}


def resolve_env(value: Any) -> Any:
    if isinstance(value, str) and value.startswith("$"):
        return os.getenv(value[1:], "")
    return value


def load_llm_config() -> dict[str, str]:
    """从 CLI 客户端的 config.toml 读取 LLM 配置"""
    config_path = Path(__file__).parent.parent.parent / "phase1-api" / "cli-chat" / "config.toml"
    if not config_path.exists():
        return DEFAULT_CONFIG

    with config_path.open("rb") as f:
        cfg = tomllib.load(f)

    result = DEFAULT_CONFIG.copy()
    result.update(cfg)
    return {k: resolve_env(v) for k, v in result.items()}


# =========================================================================
# 1. 文档加载与分块
# =========================================================================

def load_sample_document() -> str:
    """加载内部示例文档，描述本项目自身的学习路径"""
    return """# LLM 学习项目文档

## 项目概述
这是一个面向零基础人士的 AI 大模型实战学习项目。
从"5 分钟快速体验"开始，逐步深入到推理引擎、RAG、Agent 和模型微调。

## CLI 聊天客户端（cli-chat/main.py）
- 基于 OpenAI-Compatible API，用 Python 编写
- 支持 System Prompt 设定（告诉模型"你是谁"）
- 多轮对话历史以 JSON 格式保存（可以回看聊了什么）
- 流式输出，逐字实时显示
- 每次回答输出 first_token_ms 和 total_ms 指标
- 只改 config.toml 就可以切换 DeepSeek / Ollama / Proxy 三种后端

## Proxy 测试（proxy-test/）
- test_chat.py：发送一次请求，打印完整 JSON 响应
- test_stream.py：流式测试，观察逐字输出的过程

## Ollama 本地部署（ollama-notes/）
- 在 Windows 上使用 Ollama 运行自己的 AI 模型
- 数据和计算都在本机，不需要网络
- 支持 Open WebUI 作为图形界面

## 关键概念
- KV Cache：模型一边想一边写草稿纸，不用每次从头想
- 流式响应（SSE）：边生成边返回，不用等全部写完才能看
- 量化：用精度换内存——就像图片压缩，文件变小但画质略降
- 上下文窗口：模型一次能"看到"的最大字数

## 环境变量
- DEEPSEEK_API_KEY：DeepSeek API Key
- OPENAI_API_KEY：OpenAI API Key
- PROXY_API_KEY：本地 Proxy API Key
"""


def chunk_text(text: str, chunk_size: int = 300, overlap: int = 50) -> list[str]:
    """
    将长文本切分成块，块之间有一定重叠（overlap）保持上下文连贯。
    chunk_size 按字符数计算，实际生产通常按 token 数。
    """
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap

    return chunks


# =========================================================================
# 2. 向量化与检索
# =========================================================================

class SimpleVectorStore:
    """
    最简单的向量存储实现。
    生产中用 chromadb / qdrant / pinecone 替代。
    """

    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        """
        初始化 embedding 模型。
        paraphrase-multilingual-MiniLM-L12-v2 支持中文，约 400MB。
        首次运行会自动下载。
        """
        print(f"正在加载 embedding 模型：{model_name}...")
        t0 = time.perf_counter()
        self.model = SentenceTransformer(model_name)
        self.chunks: list[str] = []
        self.embeddings: np.ndarray | None = None
        print(f"模型加载完成（{int((time.perf_counter() - t0) * 1000)}ms）")

    def add_documents(self, chunks: list[str]):
        """将文档块向量化并存入索引"""
        print(f"正在向量化 {len(chunks)} 个文档块...")
        t0 = time.perf_counter()

        self.chunks = chunks
        self.embeddings = self.model.encode(chunks, show_progress_bar=True)

        print(f"向量化完成（{int((time.perf_counter() - t0) * 1000)}ms）")
        print(f"向量维度：{self.embeddings.shape[1]}")

    def search(self, query: str, top_k: int = 3) -> list[tuple[str, float]]:
        """
        搜索与 query 最相似的 top_k 个文档块。
        使用余弦相似度。
        """
        if self.embeddings is None:
            raise ValueError("请先调用 add_documents 添加文档")

        # 对查询做向量化
        query_embedding = self.model.encode([query])[0]

        # 计算余弦相似度
        # 归一化 → 点积 = 余弦相似度
        norms = np.linalg.norm(self.embeddings, axis=1, keepdims=True)
        normalized = self.embeddings / norms
        query_norm = query_embedding / np.linalg.norm(query_embedding)

        similarities = normalized @ query_norm

        # 取 top_k
        top_indices = np.argsort(similarities)[-top_k:][::-1]

        results = []
        for idx in top_indices:
            results.append((self.chunks[idx], float(similarities[idx])))

        return results


# =========================================================================
# 3. LLM 调用
# =========================================================================

def ask_llm(
    query: str,
    context_chunks: list[tuple[str, float]],
    config: dict[str, Any],
    verbose: bool = False,
) -> str:
    """
    将检索到的上下文拼成 Prompt，调用 LLM 回答。
    """
    # 拼装上下文
    context = "\n\n---\n\n".join(chunk for chunk, _ in context_chunks)

    # System prompt：告诉模型基于上下文回答
    system_prompt = (
        "你是一个技术问答助手。"
        "请基于提供的文档内容回答用户问题。"
        "如果文档内容不足以回答问题，请如实说不知道。"
        "回答时用工程师能理解的语言。"
    )

    # 构造消息
    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": (
                f"以下是相关的文档内容：\n\n{context}\n\n"
                f"请基于以上文档，回答以下问题：\n{query}"
            ),
        },
    ]

    if verbose:
        print("\n" + "=" * 60)
        print("发送给 LLM 的 Prompt：")
        print("-" * 60)
        print(f"System: {system_prompt}")
        print(f"User（含 {len(context_chunks)} 个文档块）:")
        for i, (chunk, score) in enumerate(context_chunks):
            print(f"  块 {i + 1}（相似度 {score:.3f}）：{chunk[:80]}...")
        print("=" * 60 + "\n")

    # 调用 API（复用 benchmark.py 的 HTTP 方式）
    from openai import OpenAI

    api_key = config.get("api_key", "")
    base_url = config["base_url"].rstrip("/")
    model = config.get("model", "deepseek-chat")

    client = OpenAI(api_key=api_key, base_url=base_url)

    print(f"正在请求 LLM（{model}）...")
    t0 = time.perf_counter()

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True,
        temperature=0.3,  # 问答场景用低 temperature，更确定
        max_tokens=1024,
    )

    first_token = True
    answer_parts = []

    for chunk in response:
        delta = chunk.choices[0].delta.content or ""
        if not delta:
            continue
        if first_token:
            ft = int((time.perf_counter() - t0) * 1000)
            print(f"[首 token {ft}ms]", end="", flush=True)
            first_token = False
        print(delta, end="", flush=True)
        answer_parts.append(delta)

    total = int((time.perf_counter() - t0) * 1000)
    print(f"\n[总耗时 {total}ms]")

    return "".join(answer_parts)


# =========================================================================
# 主流程
# =========================================================================

def ask_without_rag(query: str, config: dict[str, Any]):
    """不加 RAG，直接问 LLM——用于对比"""
    from openai import OpenAI

    api_key = config.get("api_key", "")
    base_url = config["base_url"].rstrip("/")
    model = config.get("model", "deepseek-chat")

    client = OpenAI(api_key=api_key, base_url=base_url)
    messages = [
        {"role": "system", "content": "你是一个技术问答助手。"},
        {"role": "user", "content": query},
    ]

    print(f"\n--- 不加 RAG，直接问 LLM ---")
    response = client.chat.completions.create(
        model=model, messages=messages, stream=True,
        temperature=0.3, max_tokens=512,
    )

    for chunk in response:
        delta = chunk.choices[0].delta.content or ""
        if delta:
            print(delta, end="", flush=True)
    print("\n")


def main():
    parser = argparse.ArgumentParser(description="RAG 检索增强生成演示")
    parser.add_argument("--query", default=None,
                        help="要查询的问题。不指定则进入交互模式")
    parser.add_argument("--top-k", type=int, default=3,
                        help="检索的文档块数量（默认 3）")
    parser.add_argument("--verbose", action="store_true",
                        help="显示详细过程信息")
    parser.add_argument("--compare", action="store_true",
                        help="对比无 RAG 的效果（直接问 LLM）")
    args = parser.parse_args()

    config = load_llm_config()

    # 1. 准备文档
    print("=" * 60)
    print("RAG 演示 — 检索增强生成")
    print("=" * 60)

    document = load_sample_document()
    chunks = chunk_text(document)
    print(f"文档已分块：{len(chunks)} 块")

    # 2. 构建向量索引
    store = SimpleVectorStore()
    store.add_documents(chunks)

    # 3. 交互循环
    while True:
        query = args.query
        if query is None:
            try:
                query = input("\n请输入问题（直接回车退出）> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not query:
                break
        else:
            # 单次查询模式
            print(f"\n问题：{query}")

        # 4. 检索
        results = store.search(query, top_k=args.top_k)

        print(f"\n检索到 {len(results)} 个相关文档块：")
        for i, (chunk, score) in enumerate(results):
            chunk_preview = chunk[:120].replace("\n", " ")
            print(f"  [{i + 1}] 相似度 {score:.3f} → {chunk_preview}...")

        # 5. 对比模式：不加 RAG
        if args.compare:
            ask_without_rag(query, config)

        # 6. LLM 回答
        answer = ask_llm(query, results, config, verbose=args.verbose)

        print(f"\n回答：{answer[:200]}...")

        # 单次查询模式
        if args.query:
            break

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
