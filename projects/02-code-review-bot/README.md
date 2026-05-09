# 综合实战 2：AI 代码审查 Bot

**综合 Phase:** 1 (API) + 4 (Agent) + 5 (Prompt) + 6 (Gateway)

**目标：** 搭建一个自动审查 Pull Request 的 Bot

**要求：**
1. 用 Phase 5 的 prompt engineering 设计一个"代码审查员"system prompt
2. 用 Phase 6 的 gateway 对外暴露 `/review` HTTP API
3. 接受一段代码，返回审查意见（安全 → 性能 → 可读性）
4. 用 Phase 6 的 logger.py 记录每次审查请求
5. 可选：用 Agent 模式添加"自动修复建议"功能

**API 设计：**
```
POST /review
Body: {"code": "...", "language": "python"}
Response: {"issues": [...], "suggestions": [...]}
```
