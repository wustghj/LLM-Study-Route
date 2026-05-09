# LLM 从零到精通 — 动手实战学习路径

> 零基础、不啃论文、不背公式。先跑起来，再理解原理。
> 30 分钟建立完整认知 → 7 个 Phase 逐步深入 → 成为 LLM 工程专家。

---

## 三条阅读路线

- **[先搞懂 LLM 到底是什么](docs/start-here.md)** — 30 分钟建立完整心智模型
- **[直接开始系统学习](docs/learning-path.md)** — 7 Phase 课程表，从 API 到源码
- **[遇到困惑查一下](docs/faq.md)** — 20 个最常见问题，随时查阅

---

## 快速开始

```powershell
# 0. 检查环境
python tools/check_env.py

# 1. 获取 API Key（platform.deepseek.com 免费注册）
$env:DEEPSEEK_API_KEY = "sk-你的key"

# 2. 装依赖 + 跑第一次对话
cd phase1-api
pip install -r requirements.txt
python main.py --config config.example.toml
```

输入问题，看屏幕上逐字出现回答。你刚完成了一次 LLM API 调用。

---

## 学习路径

```
Phase 0  基础认知        30 分钟纯阅读，建立心智模型
   ↓
Phase 1  API 精通        调 SDK、手写 HTTP、多 provider benchmark
   ↓
Phase 2  模型内部        纯 numpy 手写 Transformer 前向传播 ★
   ↓
Phase 3  本地部署        Ollama、llama.cpp、KV Cache、量化实验
   ↓
Phase 4  应用构建        RAG 检索增强 + Agent 智能体
   ↓
Phase 5  模型定制        Prompt Engineering + LoRA 微调
   ↓
Phase 6  生产上线        日志、成本、压测、网关
   ↓
Phase 7  源码深水区      llama.cpp C++ 源码阅读（可选）
```

详见 `docs/learning-path.md`。

## 项目结构

```
├── README.md                    ← 项目入口
├── CLAUDE.md                    ← Claude Code 配置
├── .gitignore
├── .github/workflows/           ← CI
│
├── docs/                        ← 📚 全部阅读材料
│   ├── start-here.md
│   ├── learning-path.md
│   ├── faq.md
│   ├── concepts/                ← Token/Embedding/Training/架构
│   ├── guides/                  ← Prompt Engineering 手册
│   └── appendix/                ← 术语表/排错/资源
│
├── phase0-fundamentals/         ← Phase 0：基础认知
├── phase1-api/                  ← Phase 1：API 精通
├── phase2-transformer/          ← Phase 2：Transformer 内部
├── phase3-local-deploy/         ← Phase 3：本地部署
├── phase4-apps/                 ← Phase 4：RAG + Agent
├── phase5-customize/            ← Phase 5：Prompt + LoRA
├── phase6-production/           ← Phase 6：日志/成本/网关
├── phase7-source/               ← Phase 7：llama.cpp 源码
│
├── projects/                    ← 🔗 综合实战
└── tools/                       ← 辅助工具
```

---

## 各 Phase 快速链接

| Phase | 目录 | 快速开始 |
|-------|------|---------|
| 0 — 基础认知 | `phase0-fundamentals/` | 读 `docs/start-here.md` |
| 1 — API 精通 | `phase1-api/` | `python main.py` |
| 2 — 模型内部 | `phase2-transformer/` | `python transformer_annotated.py` |
| 3 — 本地部署 | `phase3-local-deploy/` | `ollama pull qwen2.5:7b` |
| 4 — 应用构建 | `phase4-apps/` | `cd rag && python rag.py --compare` |
| 5 — 模型定制 | `phase5-customize/` | `cd finetune && python inference.py` |
| 6 — 生产上线 | `phase6-production/` | `python gateway.py` |
| 7 — 源码深水区 | `phase7-source/` | 读 `llama-cpp-guide.md` |

---

## 运行速查

```powershell
# Phase 1 — CLI Chat
cd phase1-api
pip install -r requirements.txt
python main.py --config config.example.toml

# Phase 2 — Transformer
cd phase2-transformer
pip install numpy
python transformer_annotated.py

# Phase 3 — 本地模型 (需先装 Ollama)
ollama pull qwen2.5:7b

# Phase 4 — RAG
cd phase4-apps/rag
pip install -r requirements.txt
python rag.py --query "什么是 KV Cache？" --compare

# Phase 4 — Agent
cd phase4-apps/agent
pip install -r requirements.txt
python agent.py

# Phase 5 — 微调
cd phase5-customize/finetune
pip install -r requirements.txt
python prepare_data.py
python train.py --model-name Qwen/Qwen2.5-1.5B-Instruct
python inference.py

# Phase 6 — 生产工具
cd phase6-production
python logger.py
python cost.py
# loadtest.py 需要: pip install aiohttp
# gateway.py 需要: pip install fastapi uvicorn aiohttp

# Phase 7 — 源码阅读
# 读 phase7-source/llama-cpp-guide.md
```

---

## 设计原则

- **Provider-agnostic**: 一个客户端，只改配置切换 DeepSeek/Ollama/Proxy
- **Minimal dependencies**: 早期 Phase 尽量少装包
- **Measurable learning**: 每次调用输出 `first_token_ms` 和 `total_ms`
- **Progressive complexity**: 每层的难度递增，没有跳跃
