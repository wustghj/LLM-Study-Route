# 综合实战 1：个人知识库问答系统

**综合 Phase:** 1 (API) + 4 (RAG)

**目标：** 搭建一个能回答你私人问题的 RAG 系统

**要求：**
1. 收集至少 5 篇与你工作/学习相关的文档（Markdown/TXT）
2. 用 Phase 4 的 RAG 代码做文档索引
3. 换更好的 embedding 模型（如 bge-large-zh-v1.5）
4. 设计 10 个测试问题，对比有/无 RAG 的回答差异
5. 优化 chunk_size——找到一个让检索最准的值

**扩展（可选）：**
- 用 Phase 6 的 gateway 对外暴露 HTTP API
- 加 cost.py 追踪每次查询的费用
- 定时更新文档库（自动化索引更新）
