# Phase 5：生产化 — 从 Demo 到服务

> 目标：把你之前写的聊天脚本，变成能上线的东西。

---

## 这一层解决什么问题

前四个 Phase 你学会了调 API、跑本地模型、构建 RAG/Agent、微调模型。但这些都是"在自己电脑上跑着玩"。

Phase 5 回答的是：**如果有人真的要用你的服务，你需要考虑什么？**

```
之前（Phase 1-4）：          Phase 5 加上：
┌─────────────────┐      ┌─────────────────┐
│ 能跑就行          │      │ 花了多少钱？      │
│ 出错重试拉倒      │  →   │ 为什么慢了？      │
│ 日志 print()     │      │ 10 个人同时用会挂吗？│
│ 没想过安全       │      │ 有人攻击怎么办？    │
└─────────────────┘      └─────────────────┘
```

---

## 四个实战项目

| Track | 项目 | 文件 | 你要回答的问题 |
|-------|------|------|--------------|
| **5A** | 结构化日志 | `logger.py` | 怎么记录每次请求的完整信息，方便排查和统计？ |
| **5B** | 成本追踪 | `cost.py` | 一次对话花了多少钱？累积了多少？ |
| **5C** | 并发压测 | `loadtest.py` | 同时 10 个人用，系统撑得住吗？瓶颈在哪？ |
| **5D** | API 网关 | `gateway.py` | 怎么做一个能上线的 LLM 服务？限流、鉴权、监控怎么做？ |

---

## 项目结构

```
production-demo/
├── README.md         ← 你在看这个
├── logger.py         ← Track 5A：结构化 JSON 日志
├── cost.py           ← Track 5B：成本计算器
├── loadtest.py       ← Track 5C：并发负载测试
├── gateway.py        ← Track 5D：最小 LLM API 网关
└── requirements.txt
```

---

## Track 5A：结构化日志（logger.py）

**核心问题：** `print()` 不是日志。你需要结构化、可查询、可聚合的日志。

**做什么：** 一个 JSON Lines 格式的日志模块。每次 LLM 请求自动记录一行 JSON，包含：
- 时间戳、请求 ID、模型、provider
- 输入/输出 token 数、首 token 延迟、总耗时
- 是否成功、错误类型
- 花费金额

**为什么用 JSON Lines：** 每行一个 JSON 对象。可以 `grep`、`jq`、导入数据库、用 Python 分析——比 print() 强一万倍。

**运行：**
```powershell
cd api调用实战/production-demo
python logger.py
```

---

## Track 5B：成本追踪（cost.py）

**核心问题：** 云 API 按 token 收费。聊得越多，花得越多。你需要知道"这一句话花了多少钱"。

**做什么：** 一个支持多 provider 的成本计算器，内置各家的定价：

| Provider | 模型 | 输入价格 | 输出价格 |
|----------|------|---------|---------|
| DeepSeek | deepseek-chat | ¥0.5/M | ¥2/M |
| OpenAI | gpt-4o | $2.5/M | $10/M |
| OpenAI | gpt-4o-mini | $0.15/M | $0.6/M |
| Ollama | 任意 | 免费 | 免费 |

> 价格会变动，以官网为准。代码里可以随时更新。

**运行：**
```powershell
python cost.py
```

---

## Track 5C：并发负载测试（loadtest.py）

**核心问题：** 你之前测的都是"一个人问一句等回答"。真实场景是很多人同时在用。并发场景下延迟怎么变？

**做什么：** 用 asyncio 并发发送大量请求，统计延迟分布和成功率。

**和 benchmark.py 的区别：**

| | benchmark.py (Phase 1) | loadtest.py (Phase 5) |
|---|---|---|
| 测试方式 | 串行，一次一个 | 并发，多个同时发 |
| 测什么 | 单个请求的延迟 | 系统在负载下的表现 |
| 指标 | first_token_ms, total_ms | P50/P95/P99 延迟, 吞吐量, 错误率 |
| 回答什么 | "这个 provider 快不快？" | "这个服务能扛多少人？" |

**运行：**
```powershell
$env:DEEPSEEK_API_KEY = "sk-..."
python loadtest.py --concurrency 5 --requests 20
```

---

## Track 5D：API 网关（gateway.py）

**核心问题：** 怎么把你的 LLM 调用封装成一个真正的服务，让别人（或你自己）通过 HTTP 调用？

**做什么：** 一个基于 FastAPI 的最小 LLM API 网关，具备：
- **路由代理** — 接收客户端请求，转发给上游（DeepSeek / Ollama）
- **API Key 鉴权** — 验证调用方身份
- **速率限制** — Token Bucket 算法，防止滥用
- **结构化日志** — 每次请求自动记录
- **流式透传** — 支持 SSE 流式响应
- **健康检查** — `/health` 端点

**架构：**
```
客户端 → Gateway (localhost:8000) → DeepSeek / Ollama
              │
              ├─ API Key 验证
              ├─ 速率限制 (Token Bucket)
              ├─ 请求日志 (JSON Lines)
              └─ 流式透传
```

**启动：**
```powershell
pip install fastapi uvicorn
$env:DEEPSEEK_API_KEY = "sk-..."
python gateway.py
# 服务跑在 http://localhost:8000
```

**然后这样用：**
```powershell
curl.exe -X POST http://localhost:8000/v1/chat/completions `
  -H "Authorization: Bearer test-key-001" `
  -H "Content-Type: application/json" `
  -d '{"model":"deepseek-chat","messages":[{"role":"user","content":"你好"}],"stream":false}'
```

---

## 后端工程师的视角

作为 C++ 后端工程师，Phase 5 的每个 Track 都直接对标你日常工作中的概念：

| Phase 5 概念 | 你的后端知识 |
|-------------|------------|
| 结构化日志 (logger.py) | JSON access log → ELK / Splunk 聚合分析 |
| 成本追踪 (cost.py) | 按量计费系统，类似云服务的 billing |
| 并发压测 (loadtest.py) | wrk / ab / JMeter，测 QPS 和 P99 延迟 |
| API 网关 (gateway.py) | Nginx / Envoy / Kong，鉴权限流路由 |
| Token Bucket | 经典限流算法，你大概率已经实现过 |
| SSE 透传 | `proxy_buffering off` + chunked response |
| 健康检查 | `/health` endpoint → K8s liveness probe |

---

## 学习路径

```
5A (logger.py)  → 5B (cost.py)  → 5C (loadtest.py)  → 5D (gateway.py)
   基础日志          算钱了          压测找瓶颈          做成服务

建议按顺序来——日志是所有生产系统的基础，先把它做好。
```

---

## 验收标准

- [ ] logger.py 能记录结构化日志，日志可以被人读懂也可以用 `jq` / Python 解析
- [ ] cost.py 能计算一次对话的费用，支持至少 2 个 provider 的价格
- [ ] loadtest.py 能并发发送请求，输出延迟分布（P50/P95/P99）和吞吐量
- [ ] gateway.py 能作为中间层代理 LLM 请求，具备限流和鉴权能力
- [ ] 能回答：你的服务在多大并发下开始明显变慢？瓶颈在哪？
